from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
import os
import uvicorn
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

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

# async def main():
#     client = MultiServerMCPClient(
#         {
#             "hotels_manipura_area": {
#                 "transport": "sse",  # HTTP-based remote server
#                 # Ensure you start your weather server on port 8000
#                 "url": "http://localhost:9000/sse",
#             }
#         }
#     )

#     tools = await client.get_tools()
#     print(tools)

    
#     llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

#     agent = create_agent(
#         model=llm,
#         tools=tools,
#     )
#     # model_with_tools = llm.bind_tools(tools)
#     # agent = create_react_agent(model_with_tools)


#     # response = await agent.ainvoke({"messages": [HumanMessage("give me hotel availability of hotel id 3")]})
#     # print(response["messages"][-1].content)

#     class ChatRequest(BaseModel):
#         message: str

#     @app.get('/chat')
#     def chat(rqeuest:ChatRequest):
#         response =agent.ainvoke({"messages": [HumanMessage("give me hotel availability of hotel id 3")]})
#         return response["messages"][-1].content


#     uvicorn.run(app, host="0.0.0.0", port=8000)

# if __name__ == "__main__":
#     asyncio.run(main())

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

@app.get('/chat')
async def chat(request:ChatRequest = Depends()):
    try:
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
        return StreamingResponse(
            event_generator(request.message),
            media_type="text/event-stream",
            headers=headers,
        )
    except Exception as e:
        return {"Error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9005)