from email.policy import default
import os
from pickle import TRUE
from fastapi import Body, FastAPI, HTTPException, Depends, Response, status
from httpx import ReadError, get
from prometheus_fastapi_instrumentator import Instrumentator
from typing import Any, Generator, Optional

from sqlalchemy import Engine
from sqlmodel import Field, Session, SQLModel, create_engine, select


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

# DATABASE_URL = "postgresql://chuck:norris@db/startrek_db"
# engine: Engine = create_engine(DATABASE_URL, echo=True)

DATABASE_URL = "sqlite:///./startrek-ships.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)
SQLModel.metadata.create_all(engine)


app = FastAPI()
Instrumentator().instrument(app).expose(app)


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
