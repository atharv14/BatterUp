from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth
from models.schemas.user import UserRole
from typing import Optional
import firebase_admin

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    try:
        token = credentials.credentials
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]

        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {str(e)}"
        )

async def get_current_user(token: dict = Depends(verify_token)):
    try:
        return token
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Could not validate credentials: {str(e)}"
        )

async def get_admin_user(token: dict = Depends(get_current_user)):
    try:
        # Check if user has admin custom claim
        if not token.get('admin', False):
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions"
            )
        return token
    except Exception as e:
        raise HTTPException(
            status_code=403,
            detail=f"Not enough permissions: {str(e)}"
        )