from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    role: str | None = None
    location: str | None = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class UserOut(UserBase):
    id: int
    class Config:
        from_attributes = True
