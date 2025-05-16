import os
import sys

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

# 加载 .env 文件
load_dotenv()


# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

mcp = FastMCP(name="weather api")

weather_key = os.environ.get("WEATHER_API_KEY")


@mcp.tool()
async def get_weather(city: str) -> str:
    """
    获取天气信息
    Args:
        city (str): 城市名称
    Returns:
        str: 天气信息
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.seniverse.com/v3/weather/daily.json",
            params={"key": weather_key, "location": city},
        )
        return response.json()


if __name__ == "__main__":
    mcp.run()
