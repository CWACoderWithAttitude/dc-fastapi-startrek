from os import name
from pydoc import cli
import select
from urllib import response
from main import Ship, app, get_session
# from main import _read_default_quotes_from_json, ChuckNorrisQuote
from httpx import Response
import pytest
from fastapi.testclient import TestClient
from fastapi import status
import random
import sys
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

DATABASE_URL = "sqlite:///./test-chuck-norris.db"
DATABASE_URL = "sqlite://"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)
# SQLModel.metadata.create_all(engine)
# Base.metadata.create_all(bind=engine)


def _generate_random_number(min_value=1, max_value=sys.maxsize):
    return random.randint(min_value, max_value)

#
# see https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/?h=pytest#client-fixture
#   for details


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_one_ship(session: Session, client: TestClient):
    input = {
        "name": "USS Dauntless",
        "sign": "NCC-80816",
        "classification": "Ship Classification"
    }
    response = client.post(
        "/ship/",
        json=input
    )
    assert response.status_code == status.HTTP_201_CREATED

    assert response.json()['name'] == input['name']
    assert response.json()['sign'] == input['sign']
    assert response.json()['classification'] == input['classification']
    assert response.json()['id'] > 0


def test_create_one_ship_full(session: Session, client: TestClient):
    input = {
        "name": "USS Franklin",
        "sign": "NX-326",
        "classification": "Starship",
        "speed": "Warp 4",
        "captain": "balthazar edison",
        "comment": "lost ~2160, first warp 4 capable ship",
        "url": "https://memory-alpha.fandom.com/wiki/Star_Trek:_The_Next_Generation"
    }
    response = client.post(
        "/ship/",
        json=input
    )
    assert response.status_code == status.HTTP_201_CREATED

    assert response.json()['name'] == input['name']
    assert response.json()['sign'] == input['sign']
    assert response.json()['classification'] == input['classification']
    assert response.json()['speed'] == input['speed']
    assert response.json()['captain'] == input['captain']
    assert response.json()['comment'] == input['comment']
    assert response.json()['url'] == input['url']
    assert response.json()['id'] > 0


def test_get_ships(session: Session, client: TestClient):
    _generate_test_ships_in_db(4, session=session)

    response = client.get("/ship/")
    assert response.status_code == 200
    list_of_ships = response.json()
    assert list_of_ships != None
    assert len(list_of_ships) == 4


def test_delete_existing_ship(session: Session, client: TestClient):
    test_ships = _generate_test_ships_in_db(10, session)
    response = client.delete("/ship/1")
    assert response.status_code == 204


def test_delete_non_existing_ship(session: Session, client: TestClient):
    test_ships = _generate_test_ships_in_db(10, session)
    response = client.delete("/ship/4711")
    assert response.status_code == 404
    assert response.json() == {"detail": "Ship 4711 not found"}


def test_get_default_ships(session: Session, client: TestClient):
    ships = client.get("/default_ships")
    assert ships.status_code == 200
    list_of_ships = ships.json()
    assert list_of_ships != None
    assert len(list_of_ships) == 44


def test_update_existing_ship(session: Session, client: TestClient):
    test_ships = _generate_test_ships_in_db(10, session)
    random = _generate_random_number()
    my_update = {
        "name": f"USS Dauntless{random}",
        "sign": f"NCC-80816{random}",
        "classification": f"Ship Classification{random}"
    }
    response = client.put(f"/ship/{test_ships[0].id}", json=my_update)
    assert response.status_code == 200
    assert response.json() != None
    assert response.json()['id'] == test_ships[0].id
    assert response.json()['name'] == my_update['name']
    assert response.json()['sign'] == my_update['sign']
    assert response.json()['classification'] == my_update['classification']


def test_update_non_existing_ship(session: Session, client: TestClient):
    test_ships = _generate_test_ships_in_db(10, session)
    random = _generate_random_number()
    my_update = {
        "name": f"USS Dauntless{random}",
        "sign": f"NCC-80816{random}",
        "classification": f"Ship Classification{random}"
    }
    response = client.put(f"/ship/4711", json=my_update)
    assert response.status_code == 404
    assert response.json() == {"detail": "Ship 4711 not found"}


def test_get_classifications(session: Session, client: TestClient):
    _generate_test_ships_in_db(5, session)
    response = client.get("/classifications")
    assert response.status_code == 200
    classifications = response.json()
    assert classifications != None
    assert len(classifications) == 15


def _generate_test_ships(number: int) -> list[Ship]:
    quotes: list[Ship] = []
    for i in range(number):
        quote = Ship(name=f"USS-Test-Ship {i}", sign=f"NCC-80816-{i}", classification=f"Ship Classification-{i}")
        quotes.append(quote)
    return quotes


def _generate_test_ships_in_db(number: int, session: Session) -> list[Ship]:
    ships: list[Ship] = _generate_test_ships(number)
    for ship in ships:
        session.add(ship)
    session.commit()
    result = session.exec(select(Ship)).all()
    return result
