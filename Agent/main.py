from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from typing import Annotated
import os
import time
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Body
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pyrate_limiter import Duration, Limiter, Rate
from fastapi_limiter.depends import RateLimiter
from utils.auth import create_access_token, verify_token
from fastapi.security import OAuth2PasswordBearer
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

origins = [

    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000/"
]


app = FastAPI();

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=api_key,
    streaming=True,
)

@app.get("/")
def read_root():
    return {"message": "Hello from the local FastAPI server!"}



class ChatRequest(BaseModel):
    message: str


def _assistant_text(message: AIMessage | AIMessageChunk) -> str:
    """Flatten assistant message content (Gemini may use str or block lists)."""
    c = message.content
    if not c:
        return ""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts: list[str] = []
        for block in c:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text" and "text" in block:
                    parts.append(str(block["text"]))
                elif "text" in block:
                    parts.append(str(block["text"]))
        return "".join(parts)
    return ""


def _sse_data_lines(text: str) -> str:
    """One SSE event; prefix each newline per https://html.spec.whatwg.org/multipage/server-sent-events.html"""
    if not text:
        return ""
   
    return "".join(f"data: {line}\n" for line in text.split("\n")) + "\n"


async def event_generator(user_input: str):
    try:
        async for chunk in llm.astream([HumanMessage(content=user_input)]):
            if isinstance(chunk, (AIMessageChunk, AIMessage)):
                text = _assistant_text(chunk)
                if text:
                    yield _sse_data_lines(text)
    except Exception as e:
        yield _sse_data_lines(f"[error] {e}")
    finally:
        yield "event: done\ndata: [DONE]\n\n"


@app.api_route(
    "/chat",
    methods=["GET", "POST"],
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(2, Duration.SECOND * 5))))],
)
async def chat(
    token: Annotated[str, Depends(oauth2_scheme)],
    message: str | None = None,
    request: ChatRequest | None = Body(default=None),
):
    try:
        print("token ----->",token , "message ----->",message, "request ----->",request)
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        exp = payload.get("exp")
        if exp and exp < time.time():
            raise HTTPException(status_code=401, detail="Token expired")

        user_message = message or (request.message if request else None)
        print("user_message ----->",user_message)
        if not user_message:
            raise HTTPException(status_code=400, detail="`message` is required")

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
        return StreamingResponse(
            event_generator(user_message),
            media_type="text/event-stream",
            headers=headers,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(req: LoginRequest):
    try:
        if req.username == "admin" and req.password == "admin":
            access_token = create_access_token(username=req.username, password=req.password)
            if not access_token:
                raise HTTPException(status_code=500, detail="Failed to generate access token")
            return {"access_token": access_token, "token_type": "bearer"}
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9005)