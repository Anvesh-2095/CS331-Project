import os
import uvicorn
from datetime import timedelta
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

import utils

# Load environment variables
load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 5))
REFRESH_TOKEN_EXPIRE_ANALYST = int(os.getenv("REFRESH_TOKEN_EXPIRE_ANALYST_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_ADMIN = int(os.getenv("REFRESH_TOKEN_EXPIRE_ADMIN_MINUTES", 60))

app = FastAPI(title="SOAR Authentication Service", version="1.0.0")

# Allow the React/HTML frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str

# --- Mock Database ---
# TODO: Replace with SQLAlchemy DB session
def mock_db_get_user(email: str):
    """Simulates a database lookup."""
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

# --- Endpoints ---

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login_for_access_token(credentials: LoginRequest):
    """
    The Common Login endpoint. 
    Authenticates the user and issues role-specific tokens.
    """
    # 1. Fetch user from DB
    user = mock_db_get_user(credentials.email)
    
    if not user or not utils.verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Determine Refresh Token expiration based on RBAC
    user_role = user["role"]
    if user_role == "admin":
        refresh_expire_time = timedelta(minutes=REFRESH_TOKEN_EXPIRE_ADMIN)
    else:
        # Default to Analyst sliding session limits
        refresh_expire_time = timedelta(minutes=REFRESH_TOKEN_EXPIRE_ANALYST)

    # 3. Generate the Tokens
    token_payload = {"sub": user["user_id"], "role": user_role}
    
    access_token = utils.create_access_token(
        data=token_payload, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = utils.create_refresh_token(
        data=token_payload, 
        expires_delta=refresh_expire_time
    )

    # TODO: Save the refresh_token to the `refresh_tokens` PostgreSQL table here

    # 4. Return tokens to frontend for RBAC Redirection
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user_role
    }

@app.get("/health")
def health_check():
    return {"status": "Auth Service Running on Port 8001"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    print(f"Starting Auth Service on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)