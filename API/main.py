from fastapi import FastAPI
app = FastAPI()
from utils.util import dummy_users_db
from utils.util import hotels_list
from login import create_access_token
from fastapi.security import OAuth2PasswordBearer
from login import verify_token
from login import verify_user_db
from fastapi import HTTPException
from fastapi import Depends
from typing import Annotated
import time

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@app.get("/hotels")
def get_hotels(token: Annotated[str, Depends(oauth2_scheme)]):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if payload["exp"] < time.time():
        raise HTTPException(status_code=401, detail="Token expired")
    return hotels_list()

@app.get("/hotels/{hotel_id}")
def get_hotel(hotel_id: int, token: Annotated[str, Depends(oauth2_scheme)]):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if payload["exp"] < time.time():
        raise HTTPException(status_code=401, detail="Token expired")
    hotel = next((hotel for hotel in hotels_list() if hotel["id"] == hotel_id), None)
    if hotel:
        return hotel
    else:
        return {"error": "Hotel not found"}     

@app.post("/login")
def login(username: str, password: str):
    try:
        verify_user = verify_user_db(username=username, password=password)
        print("verify_user", verify_user)
        if verify_user["status"] == "error":
            raise HTTPException(status_code=401, detail=verify_user["error"])
        return {"access_token": verify_user["access_token"], "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
