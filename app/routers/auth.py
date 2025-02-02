from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.utils.security import hash_password
from app.utils.email import send_verification_email
from app.utils.jwt import create_access_token,verify_token
from app.utils.security import verify_password
import uuid
from pydantic import BaseModel
from app.core.auth_guard import get_current_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/signup/", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash the password and generate verification token
        hashed_pw = hash_password(user.password)
        verification_token = str(uuid.uuid4())  # Generate UUID token

        new_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            hashed_password=hashed_pw,
            verification_token=verification_token,
            is_verified=False
        )

        # Add user to the database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Send verification email (Implement this function in `utils.py`)
        send_verification_email(user.email, verification_token)

        return new_user

    except IntegrityError:
        db.rollback()  # Rollback changes if there's a DB integrity error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error, possibly duplicate email."
        )
    
    except Exception as e:
        db.rollback()  # Rollback in case of unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.get("/verify-email/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        
        user = db.query(User).filter(User.verification_token == token).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token.")

        
        user.is_verified = True
        user.verification_token = None  # Clear token after verification
        db.commit()

        return {"message": "Email verified successfully. You can now log in."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login/")
def login(user_credentials: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Handles user login and stores JWT in an HTTP-Only Cookie."""
    try:
        user = db.query(User).filter(User.email == user_credentials.email).first()
        if not user or not verify_password(user_credentials.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        if not user.is_verified:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email before logging in.")

        # Generate JWT Token
        access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=30))
        refresh_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(days=7))

        # Store JWT in an HTTP-Only Cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=False,  # Prevent JavaScript access
            samesite="Lax",  # Prevent CSRF issues
            max_age=3600,  # 1hr expiration
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=False,
            samesite="Lax",
            max_age=604800,  # 7 days expiration
        )

        return {
            "message": "Login successful",
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))    


@router.post("/logout/")
def logout(response: Response):
    """Clears JWT by removing cookie."""
    response.delete_cookie("access_token")  
    # response.delete_cookie("refresh_token") ## deleting refresh token on logout
    return {"message": "Successfully logged out"}


@router.post("/refresh/")
def refresh_token(response: Response, request: Request):
    """Refresh the access token using the refresh token stored in cookies."""
    
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    try:
        payload = verify_token(refresh_token)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        # Generate a new access token
        new_access_token = create_access_token(data={"sub": email}, expires_delta=timedelta(minutes=30))

        # Set new access token in cookies
        response.set_cookie("access_token", new_access_token, httponly=True, samesite="Lax", max_age=1800)

        return {"message": "Access token refreshed"}

    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

@router.get("/get-token")
def get_token(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="No access token found")
    return {"access_token": access_token}
