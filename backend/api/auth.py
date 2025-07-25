# api/auth.py

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, WebSocket
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, Union

from fastapi.security import OAuth2PasswordRequestForm
from db import db_utils

# --- Configuration ---
SECRET_KEY = "your-super-secret-key-that-is-long-and-random" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# --- Router Setup ---
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# --- Pydantic Models ---
class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class User(BaseModel):
    username: str
    role: str
    is_active: bool

# --- Core Functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # ... (function content is unchanged)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependencies ---
def get_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get("access_token")

async def get_current_user(token: str | None = Depends(get_token_from_cookie)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Union[str, None] = payload.get("sub")
        role: Union[str, None] = payload.get("role")
        
        if username is None or role is None:
            raise credentials_exception
            
        # UPDATED: Return directly from inside the try block
        return TokenData(username=username, role=role)

    except JWTError:
        raise credentials_exception

async def get_current_user_from_cookie(websocket: WebSocket) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    token = websocket.cookies.get("access_token")
    if token is None:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Union[str, None] = payload.get("sub")
        role: Union[str, None] = payload.get("role")
        
        if username is None or role is None:
            raise credentials_exception
            
        # UPDATED: Return directly from inside the try block
        return TokenData(username=username, role=role)

    except JWTError:
        raise credentials_exception

def require_role(required_roles: list[str]):
    # ... (function content is unchanged)
    async def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not current_user.role or current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required role. Required: {required_roles}"
            )
        return current_user
    return role_checker

# --- API Endpoints ---
@router.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    # ... (function content is unchanged)
    user_data = db_utils.get_user_for_login(form_data.username)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    user_id, role, hashed_password = user_data
    if not verify_password(form_data.password, hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": form_data.username, "role": role}, expires_delta=access_token_expires)
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="lax", secure=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return {"status": "success", "role": role}

@router.post("/logout")
async def logout(response: Response):
    # ... (function content is unchanged)
    response.delete_cookie("access_token")
    return {"status": "success", "message": "Logged out"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: TokenData = Depends(get_current_user)):
    # ... (function content is unchanged)
    assert current_user.username is not None
    assert current_user.role is not None
    return User(username=current_user.username, role=current_user.role, is_active=True)