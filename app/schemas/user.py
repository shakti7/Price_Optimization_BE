from pydantic import BaseModel, EmailStr, Field, validator


class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, description="First name is required and must be within 50 characters.")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name is required and must be within 50 characters.")
    email: EmailStr = Field(..., description="Valid email is required.")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long.")

    @validator("password")
    def validate_password(cls, value):
        
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return value


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Valid email is required.")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long.")


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    is_verified: bool

    class Config:
        from_attributes = True  

class UserResponseBody(BaseModel):
    status_code: str
    status: str
    data: dict
    message: str