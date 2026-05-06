import jwt
import os 
from dotenv import load_dotenv
load_dotenv()
SECREAT_KEY = os.getenv("SECREAT_KEY")
ALGORITHM = os.getenv("ALGORITHM")


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECREAT_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def create_access_token(username:str, password:str):
    try:
        to_encode = {
            "username":username,
        }
        return jwt.encode(to_encode, SECREAT_KEY, algorithm=ALGORITHM)
    except Exception as e:
        return None