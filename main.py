from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
import jwt
from email.policy import default
import os
from pickle import TRUE
from fastapi import Body, FastAPI, HTTPException, Depends, Response, status
from httpx import ReadError, get
from prometheus_fastapi_instrumentator import Instrumentator
from typing import Any, Generator, Optional

from sqlalchemy import Engine, SQLColumnExpression
from sqlmodel import Field, Session, SQLModel, create_engine, select

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
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


db_name: str = os.environ.get("db_name", "<MY-DB-NAME>")
db_user: str = os.environ.get("db_user", "<MY-DB-USER>")
db_password: str = os.environ.get("db_password", "<MY-DB-PASSWD>")
# DATABASE_URL = f"postgresql://{db_user}:${db_password}@db/{db_name}"
# DATABASE_URL = "postgresql://chuck:norris@db/chuck_norris_db"

# engine: Engine = create_engine(DATABASE_URL, echo=True)

DATABASE_URL = "postgresql://star:trek@db/star-trek-ships-db"
# DATABASE_URL = "sqlite:///./startrek-ships.db"
# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)
engine = create_engine(DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)


app = FastAPI()
Instrumentator().instrument(app).expose(app)

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


@app.post("/token")
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


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]
# end oauth2 stuff


def get_session() -> Generator[Session, Any, None]:
    with Session(engine) as session:
        yield session


@app.post("/ship/", response_model=Ship, tags=["starek", "ships"], status_code=status.HTTP_201_CREATED)
def create_chuck_norris(ship: Ship, session: Session = Depends(get_session)):
    session.add(ship)
    session.commit()
    session.refresh(ship)
    return ship


@app.get(f"/ship/", response_model=list[Ship], tags=["starek", "ships"], status_code=status.HTTP_200_OK)
def get_ships(skip: int = 0, limit: int = 10, session: Session = Depends(get_session)):
    ships = session.exec(select(Ship).offset(skip).limit(limit)).all()
    return ships


@app.delete("/ship/{ship_id}", tags=["starek", "ships"], status_code=status.HTTP_204_NO_CONTENT)
def delete_ship(ship_id: int, session: Session = Depends(get_session)):
    ship = session.get(Ship, ship_id)

    if ship is None:
        raise HTTPException(status_code=404, detail=f"Ship {ship_id} not found")
    session.delete(ship)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# @app.get(f"/chuck_norris/", response_model=list[ChuckNorrisQuote], tags=["quotes"])
# def get_quotes(skip: int = 0, limit: int = 10, session: Session = Depends(get_session)):
#     print(f"get_quotes: {skip}, {limit}")
#     quotes = session.exec(select(ChuckNorrisQuote).offset(skip).limit(limit)).all()
#     return quotes


# @app.get('/chuck_norris/{quote_id}', response_model=ChuckNorrisQuote, tags=["quotes"])
# def get_quote(quote_id: int, session: Session = Depends(get_session)):
#     quote = session.get(ChuckNorrisQuote, quote_id)
#     if quote is None:
#         raise HTTPException(status_code=404, detail=f"Quote {quote_id} not found")
#     return quote


# @app.delete("/chuck_norris/{quote_id}", tags=["quotes"])
# def delete_quote(quote_id: int, session: Session = Depends(get_session)):
#     quote = session.get(ChuckNorrisQuote, quote_id)
#     if quote is None:
#         raise HTTPException(status_code=404, detail=f"Quote {quote_id} not found")
#     session.delete(quote)
#     session.commit()
#     return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.put("/ship/{quote_id}", tags=["startrek", "ships"])
def update_ship(quote_id: int, ship_update: Ship, session: Session = Depends(get_session)):
    db_ship = session.get(Ship, quote_id)
    if db_ship is None:
        raise HTTPException(status_code=404, detail=f"Ship {quote_id} not found")
    db_ship.name = ship_update.name
    db_ship.classification = ship_update.classification
    db_ship.sign = ship_update.sign

    session.commit()
    session.refresh(db_ship)
    return db_ship
# def update_quote(quote_id: int, quote_update: ChuckNorrisQuote, session: Session = Depends(get_session)):
#     db_quote = session.get(ChuckNorrisQuote, quote_id)
#     if db_quote is None:
#         raise HTTPException(status_code=404, detail=f"Quote {quote_id} not found")
#     db_quote.quote = quote_update.quote
#     db_quote.language = quote_update.language
#     session.commit()
#     session.refresh(db_quote)
#     print(f"updated quote: {db_quote}")
#     return db_quote


def _read_default_ships_from_json():
    import json
    with open("ships_full.json", "r") as file:
        ships = json.load(file)
    return ships


# @app.get("/default_quotes", response_model=list[ChuckNorrisQuote], tags=["admin"])
# def insert_default_quotes(session: Session = Depends(get_session)):
#     default_quotes = _read_default_quotes_from_json()
#     for quote in default_quotes:
#         cn = ChuckNorrisQuote(**quote)
#         session.add(cn)
#     session.commit()
#     return session.exec(select(ChuckNorrisQuote)).all()
@app.get("/default_ships", response_model=list[Ship], tags=["admin", "startrek", "ships"])
def insert_default_quotes(session: Session = Depends(get_session)):
    default_ships = _read_default_ships_from_json()
    for ship in default_ships:
        s = Ship(**ship)
        session.add(s)
    session.commit()
    return session.exec(select(Ship)).all()


# @app.get("/", tags=["root"])
# def root():
#     endpoints: dict[str, str] = {}
#     endpoints["root"] = "/"
#     endpoints["Swagger UI"] = "/docs"
#     endpoints["ReDoc"] = "/redoc"
#     endpoints["Get all quotes"] = "/chuck_norris/"
#     endpoints["/default_quotes"] = "Insert default quotes"
#     endpoints["Grafana"] = "http://:9730"
#     endpoints["Prometheus"] = "http://localhost:9790"
#     endpoints["DB Adminer"] = "http://localhost:9710"
#     return endpoints


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
