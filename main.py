import logging
from multiprocessing import Queue
from logging_loki import LokiQueueHandler
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
import jwt
from email.policy import default
import os
from pickle import TRUE
from fastapi import FastAPI, HTTPException, Depends, Response, status
from httpx import get
from prometheus_fastapi_instrumentator import Instrumentator
from typing import Any, Generator, Optional
from pydantic_settings import BaseSettings

from sqlalchemy import Engine, SQLColumnExpression
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Settings(BaseSettings):
    # db_name: str = None  # os.environ.get("db_name", "<MY-DB-NAME>")
    # db_user: str = None  # os.environ.get("db_user", "<MY-DB-USER>")
    # db_password: None  # str = os.environ.get("db_password", "<MY-DB-PASSWD>")
    # secret_key: str = None
    # algorithm: str = None
    # os.environ.get("db_url", "<MY-DB-URL>")  # "postgresql://star:trek@db/star-trek-ships-db"
    db_url: str = ""
    SECRET_KEY: str = ""
    ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 0
    LOKI_ENDPOINT: str = "http://loki:3100/loki/api/v1/push"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    },
    "volker": {
        "username": "volker",
        "full_name": "JavaVolker",
        "email": "CWA.Coder.With.AttitudeAtgmail.com",
        "hashed_password": "$2b$12$XSeIVJPWjKQvfoP2I/9pXe6FMPpIRYA55Xr.T613A2kZWDvRl5DWm",
        "disabled": False
    }
}


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: str | None = None


class User(SQLModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Ship(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    classification: str = Field(index=True)
    sign: str | None = Field(default=None, index=True)
    speed: str | None = Field(default=None, index=True)
    captain: str | None = Field(default=None, index=True)
    comment: str | None = Field(default=None, index=True)
    url: str | None = Field(default=None, index=True)


settings = Settings()

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = settings.SECRET_KEY  # 09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


DATABASE_URL = settings.db_url
engine = create_engine(DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)

app = FastAPI()
Instrumentator().instrument(app).expose(app)

loki_logs_handler = LokiQueueHandler(
    Queue(-1),
    url=settings.LOKI_ENDPOINT,
    tags={"application": "fastapi"},
    version="1",
)

uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addHandler(loki_logs_handler)
# oauth2 stuff


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    return pwd_context.hash(password)


def get_user(db, username: str) -> UserInDB | None:
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str) -> UserInDB | Literal[False]:
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.get("/info", tags=["info"])
def get_info() -> dict[str, Any]:
    """
    Get info about the API
    """
    return settings.model_dump()


@app.post("/token", tags=["oauth2"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=User, tags=["secure"])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@app.get("/users/me/items/", tags=["secure"])
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.email}]
# end oauth2 stuff


def get_session() -> Generator[Session, Any, None]:
    with Session(engine) as session:
        yield session


@app.post("/ship/", response_model=Ship, tags=["startrek", "ships"], status_code=status.HTTP_201_CREATED)
async def create_ship(ship: Ship, session: Session = Depends(get_session)):
    session.add(ship)
    session.commit()
    session.refresh(ship)
    return ship


@app.post("/ship_secure/", response_model=Ship, tags=["startrek", "ships"], status_code=status.HTTP_201_CREATED)
async def create_ship(ship: Ship, current_user: Annotated[User, Depends(get_current_active_user)], session: Session = Depends(get_session)) -> Ship:
    ship.comment = f"created by {current_user.email}"
    session.add(ship)
    session.commit()
    session.refresh(ship)
    return ship


@app.get(f"/ship/", response_model=list[Ship], tags=["startrek", "ships"], status_code=status.HTTP_200_OK)
async def get_ships(skip: int = 0, limit: int = 10, session: Session = Depends(get_session)):
    ships = session.exec(select(Ship).offset(skip).limit(limit)).all()
    return ships


@app.get("/classifications", response_model=list[str], tags=["startrek", "classifications"])
async def get_classifications(session: Session = Depends(get_session)) -> list[str]:
    """
    Get distinct list of known ship classifications
    """
    ships = session.exec(select(Ship)).all()
    classifications = set()
    for ship in ships:
        classifications.add(ship.classification)
    # classifications = [c['classification'] for c in classifications]
    return list(classifications)


@app.delete("/ship/{ship_id}", tags=["startrek", "ships"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_ship(ship_id: int, session: Session = Depends(get_session)):
    ship = session.get(Ship, ship_id)

    if ship is None:
        raise HTTPException(status_code=404, detail=f"Ship {ship_id} not found")
    session.delete(ship)
    session.commit()


@app.put("/ship_secure/{ship_id}", tags=["startrek", "ships"])
async def update_ship_secure(ship_id: int, current_user: Annotated[User, Depends(get_current_active_user)], ship_update: Ship, session: Session = Depends(get_session)):
    db_ship = session.get(Ship, ship_id)
    if db_ship is None:
        raise HTTPException(status_code=404, detail=f"Ship {ship_id} not found")
    db_ship.name = ship_update.name
    db_ship.classification = ship_update.classification
    db_ship.sign = ship_update.sign
    db_ship.url = ship_update.url
    db_ship.comment = f"Last updated by {current_user.email}"

    session.commit()
    session.refresh(db_ship)
    return db_ship


@app.put("/ship/{ship_id}", tags=["startrek", "ships"])
async def update_ship(ship_id: int, ship_update: Ship, session: Session = Depends(get_session)):
    db_ship = session.get(Ship, ship_id)
    if db_ship is None:
        raise HTTPException(status_code=404, detail=f"Ship {ship_id} not found")
    db_ship.name = ship_update.name
    db_ship.classification = ship_update.classification
    db_ship.sign = ship_update.sign
    db_ship.url = ship_update.url

    session.commit()
    session.refresh(db_ship)
    return db_ship


@app.put("/ship_secure/{ship_id}", tags=["startrek", "ships"])
async def update_ship_secure(ship_id: int, current_user: Annotated[User, Depends(get_current_active_user)], ship_update: Ship, session: Session = Depends(get_session)):
    db_ship = session.get(Ship, ship_id)
    if db_ship is None:
        raise HTTPException(status_code=404, detail=f"Ship {ship_id} not found")
    db_ship.name = ship_update.name
    db_ship.classification = ship_update.classification
    db_ship.sign = ship_update.sign
    db_ship.comment = f"Last updated by {current_user.email}"

    session.commit()
    session.refresh(db_ship)
    return db_ship


def _read_default_ships_from_json():
    import json
    with open("ships_full.json", "r") as file:
        ships = json.load(file)
    return ships


@app.get("/default_ships", response_model=list[Ship], tags=["admin", "startrek", "ships"])
async def insert_default_ships(session: Session = Depends(get_session)):
    default_ships = _read_default_ships_from_json()
    for ship in default_ships:
        s = Ship(**ship)
        session.add(s)
    session.commit()
    return session.exec(select(Ship)).all()


@app.get("/", tags=["root"])
async def root():
    endpoints: dict[str, str] = {}
    endpoints["root"] = "/"
    endpoints["Swagger UI"] = "/docs"
    endpoints["ReDoc"] = "/redoc"
    endpoints["Grafana"] = "http://:9630"
    endpoints["Prometheus"] = "http://:9690"
    endpoints["DB Adminer"] = "http://:9610"
    return endpoints
