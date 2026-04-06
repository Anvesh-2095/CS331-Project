import os
import uvicorn
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, status, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import uuid

import utils
from database import engine, Base, get_db
import models

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 5))
REFRESH_TOKEN_EXPIRE_ANALYST = int(os.getenv("REFRESH_TOKEN_EXPIRE_ANALYST_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_ADMIN = int(os.getenv("REFRESH_TOKEN_EXPIRE_ADMIN_MINUTES", 60))

app = FastAPI(title="SOAR Authentication & Execution API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Models ---
class LoginRequest(BaseModel):
    email: str # EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str

class CommandRequest(BaseModel):
    command: str

# --- Security Dependency ---
async def get_current_user_role(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        role: str = payload.get("role")
        if role is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return role
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# --- Endpoints ---
@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Fetch user from PostgreSQL
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    
    if not user or not utils.verify_password(credentials.password, user.password_hash):
        # Log failure to DB and RabbitMQ
        db_log = models.AuthAuditLog(email_attempted=credentials.email, status="FAILED_PASSWORD")
        db.add(db_log)
        db.commit()
        background_tasks.add_task(utils.publish_audit_log, event_type="AUTH_LOGIN", user_email=credentials.email, status="FAILURE")
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # 2. Determine Expiration based on RBAC Enum
    user_role = user.role.value
    refresh_expire_minutes = REFRESH_TOKEN_EXPIRE_ADMIN if user_role == "admin" else REFRESH_TOKEN_EXPIRE_ANALYST
    refresh_expire = timedelta(minutes=refresh_expire_minutes)
    token_payload = {"sub": str(user.user_id), "role": user_role}
    
    # 3. Generate Tokens
    access_token = utils.create_access_token(data=token_payload, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token_string = utils.create_refresh_token(data=token_payload, expires_delta=refresh_expire)

    # 4. Save Refresh Token and Update User Activity in DB
    db_token = models.RefreshToken(
        user_id=user.user_id,
        token_string=refresh_token_string,
        expires_at=datetime.utcnow() + refresh_expire
    )
    user.last_active_at = datetime.utcnow()
    db_log = models.AuthAuditLog(email_attempted=credentials.email, status="SUCCESS")
    
    db.add_all([db_token, db_log])
    db.commit()

    background_tasks.add_task(utils.publish_audit_log, event_type="AUTH_LOGIN", user_email=credentials.email, status="SUCCESS", details={"role": user_role})

    return {"access_token": access_token, "refresh_token": refresh_token_string, "token_type": "bearer", "role": user_role}

@app.post("/api/v1/auth/refresh", response_model=TokenResponse)
async def refresh_session(req: RefreshRequest, db: Session = Depends(get_db)):
    try:
        # 1. Check if token exists in DB and is not revoked
        db_token = db.query(models.RefreshToken).filter(models.RefreshToken.token_string == req.refresh_token).first()
        if not db_token or db_token.is_revoked or db_token.expires_at < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        # 2. Decode existing token
        payload = jwt.decode(req.refresh_token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if not user_id or payload.get("token_type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token payload")

        # 3. Issue new tokens
        refresh_expire_minutes = REFRESH_TOKEN_EXPIRE_ADMIN if role == "admin" else REFRESH_TOKEN_EXPIRE_ANALYST
        refresh_expire = timedelta(minutes=refresh_expire_minutes)
        token_payload = {"sub": user_id, "role": role}
        
        new_access = utils.create_access_token(data=token_payload, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        new_refresh = utils.create_refresh_token(data=token_payload, expires_delta=refresh_expire)

        # 4. Revoke old token and save new one
        db_token.is_revoked = True
        new_db_token = models.RefreshToken(
            user_id=uuid.UUID(user_id),
            token_string=new_refresh,
            expires_at=datetime.utcnow() + refresh_expire
        )
        
        # Update user activity
        user = db.query(models.User).filter(models.User.user_id == uuid.UUID(user_id)).first()
        if user:
            user.last_active_at = datetime.utcnow()

        db.add(new_db_token)
        db.commit()

        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer", "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token cryptographic signature invalid")

@app.post("/api/v1/soar/execute")
async def execute_cli_command(req: CommandRequest, role: str = Depends(get_current_user_role)):
    command = req.command.lower().strip()
    
    if command == "whoami":
        return {"output": f"Authenticated as: {role.upper()}"}
        
    elif command.startswith("isolate"):
        if role != "admin":
            return {"output": "Access Denied: Only Admins can isolate hosts."}
            
        parts = command.split(" ")
        if len(parts) != 2:
            return {"output": "Usage: isolate <ip_address>"}
            
        target_ip = parts[1]
        
        success = utils.publish_action_to_rabbitmq(
            action="isolate_network", 
            target=target_ip, 
            user=role
        )
        
        if success:
            return {"output": f"[+] Command dispatched! Agent on {target_ip} instructed to isolate network."}
        else:
            return {"output": "[-] Error: Message Broker (RabbitMQ) is unreachable."}
            
    else:
        return {"output": f"Command not recognized: {req.command}. Try 'isolate 10.0.0.5'"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    print(f"Starting API on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)