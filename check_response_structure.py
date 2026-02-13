"""
Check actual API response structure
"""
import asyncio
import httpx
from app.core.config import settings
import json


async def check_response():
    headers = {
        "X-APP-ID": settings.CHARTEX_APP_ID,
        "X-APP-TOKEN": settings.CHARTEX_APP_TOKEN,
    }
    
    params = {"limit": 2}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://api.chartex.com/external/v1/songs/",
            headers=headers,
            params=params
        )
        
        print(f"Status: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            print("Full Response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")


if __name__ == "__main__":
    asyncio.run(check_response())
