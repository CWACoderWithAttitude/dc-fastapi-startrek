# app/model.py

from pydantic import BaseModel, EmailStr, Field




class BoardGameCreate(BaseModel):
    title: str
    publisher: str
    min_number_of_players: int
    max_number_of_players: int
    typical_duration: int
    ean13: str
    min_age: int


class UserSchema(BaseModel):
    fullname: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "fullname": "Abdulazeez Abdulazeez Adeshina",
                "email": "abdulazeez@x.com",
                "password": "weakpassword"
            }
        }


class UserLoginSchema(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "abdulazeez@x.com",
                "password": "weakpassword"
            }
        }
