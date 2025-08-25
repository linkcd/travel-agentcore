import random
from mcp.server.fastmcp import FastMCP 

mcp = FastMCP(host="0.0.0.0", stateless_http=True)  

@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather for a city"""
    conditions = ["Sunny", "Cloudy", "Rainy", "Partly cloudy", "Foggy", "Snowy", "Windy"]
    condition = random.choice(conditions)
    temperature = random.randint(-10, 35)
    return f"{condition}, {temperature}°C in {city}"

@mcp.tool()
def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city"""
    min_temp = random.randint(-5, 20)
    max_temp = random.randint(min_temp + 5, 35)
    conditions = ["sunny", "cloudy", "rainy", "mixed conditions"]
    condition = random.choice(conditions)
    return f"{days}-day forecast for {city}: Mostly {condition} with temperatures ranging {min_temp}-{max_temp}°C"

if __name__ == "__main__": 
    mcp.run(transport="streamable-http")
