from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import asyncio
import os
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

app = FastAPI();



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

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

agent = create_agent(
        model=llm
    )
class ChatRequest(BaseModel):
    message: str

@app.get('/chat')
def chat(rqeuest:ChatRequest):
    print ("hello here")
    response =agent.ainvoke({"messages": [HumanMessage("give me hotel availability of hotel id 3")]})
        # return response["messages"][-1].content
    return "hello"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9005)