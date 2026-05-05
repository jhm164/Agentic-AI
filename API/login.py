

import jwt
import os 
from dotenv import load_dotenv
from utils.util import dummy_users_db
from datetime import datetime, timedelta
load_dotenv()
SECREAT_KEY = os.getenv("SECREAT_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")


def create_access_token(data: dict):
    try:
        to_encode = {
            "username": data["username"],
            "full_name": data["full_name"],
            "email": data["email"]
        } # find why we are copying the data
        print(to_encode)
        expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECREAT_KEY, algorithm=ALGORITHM)
        print(encoded_jwt)
        return encoded_jwt
    except Exception as e:
        print(e)
        return { "error": str(e) }



def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECREAT_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def verify_user_db(username: str, password: str):
    try:
        user = dummy_users_db()
        print(user)
        print(user["username"])
        if user["username"] == username and user["password"] == password:
                return { "status": "success", "access_token": create_access_token(data=user) }
        else:
                return { "status": "error", "error": "Invalid credentials" }
    except Exception as e:
        print(e)
        return { "error": str(e) }