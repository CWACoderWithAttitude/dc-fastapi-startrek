# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.responses import Response
# from sqlmodel import Session
# from model.ship_model import Ship
# from main import get_session
# from typing import List
# from sqlalchemy import select

# router = APIRouter()


# @router.post("/ship/", response_model=Ship, tags=["startrek", "ships"], status_code=status.HTTP_201_CREATED)
# async def create_ship(ship: Ship, session: Session = Depends(get_session)):
#     session.add(ship)
#     session.commit()
#     session.refresh(ship)
#     return ship
