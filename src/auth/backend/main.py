import os
import uvicorn
from datetime import timedelta
from fastapi import FastAPI, HTTPException, status, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from dotenv import load_dotenv

import utils

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 5))
REFRESH_TOKEN_EXPIRE_ANALYST = int(os.getenv("REFRESH_TOKEN_EXPIRE_ANALYST_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_ADMIN = int(os.getenv("REFRESH_TOKEN_EXPIRE_ADMIN_MINUTES", 60))

app = FastAPI(title="SOAR Authentication & Execution API")

# Allow the separate HTML frontend to communicate with this API
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
    email: EmailStr
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

# --- Mock Database ---
def mock_db_get_user(email: str):
    mock_users = {
        "analyst@soar.local": {
            "user_id": "1111-2222",
            "password_hash": utils.get_password_hash("password123"),
            "role": "analyst"
        },
        "admin@soar.local": {
            "user_id": "3333-4444",
            "password_hash": utils.get_password_hash("admin123"),
            "role": "admin"
        }
    }
    return mock_users.get(email)

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
async def login(credentials: LoginRequest, background_tasks: BackgroundTasks):
    user = mock_db_get_user(credentials.email)
    
    if not user or not utils.verify_password(credentials.password, user["password_hash"]):
        background_tasks.add_task(
            utils.publish_audit_log, event_type="AUTH_LOGIN", user_email=credentials.email, status="FAILURE"
        )
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    user_role = user["role"]
    refresh_expire = timedelta(minutes=REFRESH_TOKEN_EXPIRE_ADMIN if user_role == "admin" else REFRESH_TOKEN_EXPIRE_ANALYST)
    token_payload = {"sub": user["user_id"], "role": user_role}
    
    access_token = utils.create_access_token(data=token_payload, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = utils.create_refresh_token(data=token_payload, expires_delta=refresh_expire)

    background_tasks.add_task(
        utils.publish_audit_log, event_type="AUTH_LOGIN", user_email=credentials.email, status="SUCCESS", details={"role": user_role}
    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "role": user_role}

@app.post("/api/v1/auth/refresh", response_model=TokenResponse)
async def refresh_session(req: RefreshRequest):
    try:
        payload = jwt.decode(req.refresh_token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if not user_id or payload.get("token_type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        refresh_expire = timedelta(minutes=REFRESH_TOKEN_EXPIRE_ADMIN if role == "admin" else REFRESH_TOKEN_EXPIRE_ANALYST)
        token_payload = {"sub": user_id, "role": role}
        
        new_access = utils.create_access_token(data=token_payload, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        new_refresh = utils.create_refresh_token(data=token_payload, expires_delta=refresh_expire)

        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer", "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expired")

@app.post("/api/v1/soar/execute")
async def execute_cli_command(req: CommandRequest, role: str = Depends(get_current_user_role)):
    command = req.command.lower().strip()
    
    if command == "whoami":
        return {"output": f"Authenticated as: {role.upper()}"}
        
    # Example command format: "isolate 10.0.0.5"
    elif command.startswith("isolate"):
        if role != "admin":
            return {"output": "Access Denied: Only Admins can isolate hosts."}
            
        parts = command.split(" ")
        if len(parts) != 2:
            return {"output": "Usage: isolate <ip_address>"}
            
        target_ip = parts[1]
        
        # Fire the message into RabbitMQ!
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