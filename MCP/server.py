from fastmcp import FastMCP
import requests
import logging
from dotenv import load_dotenv
import os
load_dotenv()

API_URL = os.getenv("API_URL")
from fastmcp.server.dependencies import get_http_headers

fastmcp = FastMCP(name="Hotels in Manipura area MCP")
# Basic setup to log to a file with a specific format and level
logging.basicConfig(
    filename='server.log',
    filemode='a', # 'a' for append, 'w' for overwrite
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

@fastmcp.tool()
def get_hotels():
    """Get all hotels in Manipura area"""
    headers =  get_http_headers(include_all=True)
    print("headers===", headers)
    try:
        response = requests.get("http://localhost:8000/hotels", headers=headers)
        # logging.info(response)
        return response.json()
    except Exception as e:
        logging.error(e)
        return {"error": str(e)}
    return  {"theme": "dark", "version": "1.0"}

@fastmcp.tool()
def get_hotel(hotel_id: int):
    """ Get a specific hotel in Manipura area by id"""
    try:
        headers =  get_http_headers(include_all=True)
        print("headers===", headers)
        response = requests.get(f"http://localhost:8000/hotels/{hotel_id}", headers=headers )
        # logger.info(response)
        return response.json()
    except Exception as e:
        logging.error(e)
        return {"error": str(e)}
    return  {"theme": "dark", "version": "1.0"}


if __name__ == "__main__":
    fastmcp.run(transport="sse",port=9000)