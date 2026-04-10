"""MCP Weather Server - 天气查询服务."""

from fastmcp import FastMCP
import random
from datetime import date, timedelta

# 创建 MCP 服务器
mcp = FastMCP("WeatherService")


# 模拟城市天气基数（用于生成"一致"的随机数据）
CITY_WEATHER_BASE = {
    "paris": {"temp": 18, "humidity": 65},
    "istanbul": {"temp": 22, "humidity": 60},
    "london": {"temp": 15, "humidity": 75},
    "new york": {"temp": 20, "humidity": 55},
    "tokyo": {"temp": 23, "humidity": 70},
    "berlin": {"temp": 16, "humidity": 60},
    "rome": {"temp": 24, "humidity": 50},
    "madrid": {"temp": 26, "humidity": 40},
    "amsterdam": {"temp": 15, "humidity": 70},
    "beijing": {"temp": 21, "humidity": 45},
    "shanghai": {"temp": 22, "humidity": 65},
    "dubai": {"temp": 35, "humidity": 30},
    "singapore": {"temp": 30, "humidity": 80},
    "bangkok": {"temp": 32, "humidity": 75},
    "sydney": {"temp": 22, "humidity": 55},
}

WEATHER_CONDITIONS = [
    "sunny", "clear", "partly cloudy", "cloudy",
    "rainy", "light rain", "heavy rain", "thunderstorm",
    "windy", "foggy", "snow", "light snow"
]

CONDITION_ICONS = {
    "sunny": "☀️", "clear": "🌙", "partly cloudy": "⛅", "cloudy": "☁️",
    "rainy": "🌧️", "light rain": "🌦️", "heavy rain": "⛈️", "thunderstorm": "⚡",
    "windy": "💨", "foggy": "🌫️", "snow": "❄️", "light snow": "🌨️"
}


def get_weather_base(city: str) -> dict:
    """获取城市天气基数（用于生成一致的数据）."""
    city_lower = city.lower()
    for name, base in CITY_WEATHER_BASE.items():
        if name in city_lower:
            return base
    # 默认值
    return {"temp": 20, "humidity": 60}


def generate_current_weather(city: str) -> dict:
    """生成当前天气数据."""
    base = get_weather_base(city)
    condition = random.choice(WEATHER_CONDITIONS)

    return {
        "city": city,
        "timestamp": date.today().isoformat(),
        "temperature": base["temp"] + random.randint(-3, 3),
        "feels_like": base["temp"] + random.randint(-5, 2),
        "condition": condition,
        "icon": CONDITION_ICONS.get(condition, "🌡️"),
        "humidity": base["humidity"] + random.randint(-10, 10),
        "wind_speed": random.randint(0, 40),
        "wind_direction": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
        "pressure": random.randint(1000, 1030),
        "visibility": random.randint(5, 20),
        "uv_index": random.randint(0, 11),
    }


def generate_forecast(city: str, days: int = 7) -> list[dict]:
    """生成天气预报数据."""
    base = get_weather_base(city)
    forecast = []

    for i in range(days):
        forecast_date = date.today() + timedelta(days=i)
        condition = random.choice(WEATHER_CONDITIONS)

        forecast.append({
            "date": forecast_date.isoformat(),
            "day_of_week": forecast_date.strftime("%A"),
            "temp_high": base["temp"] + random.randint(0, 5),
            "temp_low": base["temp"] - random.randint(0, 5),
            "condition": condition,
            "icon": CONDITION_ICONS.get(condition, "🌡️"),
            "precipitation_chance": random.randint(0, 100) if "rain" in condition else random.randint(0, 30),
            "humidity": base["humidity"] + random.randint(-15, 15),
            "wind_speed": random.randint(0, 35),
        })

    return forecast


@mcp.tool()
def get_current_weather(city: str) -> str:
    """
    获取指定城市的当前天气.

    :param city: 城市名称 (如 Paris, Istanbul, Beijing)
    """
    weather = generate_current_weather(city)

    result = f"🌤️ Current Weather in {weather['city']}\n\n"
    result += f"   {weather['icon']} {weather['condition'].title()}\n"
    result += f"   🌡️  温度：{weather['temperature']}°C (体感：{weather['feels_like']}°C)\n"
    result += f"   💧 湿度：{weather['humidity']}%\n"
    result += f"   💨 风速：{weather['wind_speed']} km/h ({weather['wind_direction']})\n"
    result += f"   👁️ 能见度：{weather['visibility']} km\n"
    result += f"   ☀️ 紫外线指数：{weather['uv_index']}\n"
    result += f"   📊 气压：{weather['pressure']} hPa\n"

    return result


@mcp.tool()
def get_weather_forecast(city: str, days: int = 7) -> str:
    """
    获取指定城市的天气预报.

    :param city: 城市名称
    :param days: 预报天数 (1-14 天，默认 7 天)
    """
    if days < 1:
        days = 1
    if days > 14:
        days = 14

    forecast = generate_forecast(city, days)

    result = f"📅 {days}-Day Weather Forecast for {city}\n\n"

    for day in forecast:
        result += f"   {day['day_of_week']} ({day['date']}):\n"
        result += f"      {day['icon']} {day['temp_low']}°C ~ {day['temp_high']}°C | {day['condition'].title()}\n"
        if day['precipitation_chance'] > 30:
            result += f"      🌧️ 降水概率：{day['precipitation_chance']}%\n"
        result += f"      💨 风速：{day['wind_speed']} km/h | 💧 湿度：{day['humidity']}%\n\n"

    return result


@mcp.tool()
def get_travel_weather_advice(
    origin: str,
    destination: str,
    travel_date: str,
) -> str:
    """
    获取旅行天气建议.

    :param origin: 出发城市
    :param destination: 目的地城市
    :param travel_date: 旅行日期 (YYYY-MM-DD)
    """
    dest_weather = generate_current_weather(destination)
    dest_forecast = generate_forecast(destination, 5)

    # 生成建议
    advice = []

    if dest_weather["temperature"] > 30:
        advice.append("☀️ 目的地天气炎热，建议携带防晒霜、太阳镜和轻便衣物")
    elif dest_weather["temperature"] < 10:
        advice.append("❄️ 目的地天气寒冷，建议携带厚外套、保暖衣物")
    elif dest_weather["temperature"] < 20:
        advice.append("🍃 目的地天气凉爽，建议携带薄外套")

    if "rain" in dest_weather["condition"]:
        advice.append("☔ 目的地有雨，请携带雨具")

    if dest_weather["wind_speed"] > 30:
        advice.append("💨 目的地风力较大，注意防风")

    if dest_weather["uv_index"] > 7:
        advice.append("☀️ 紫外线强度高，请注意防晒")

    if not advice:
        advice.append("👍 目的地天气良好，适合旅行")

    result = f"🧳 Travel Weather Advice\n\n"
    result += f"   出发地：{origin}\n"
    result += f"   目的地：{destination}\n"
    result += f"   旅行日期：{travel_date}\n\n"
    result += f"   当前天气：{dest_weather['icon']} {dest_weather['temperature']}°C\n\n"
    result += f"   📋 建议:\n"
    for adv in advice:
        result += f"      {adv}\n"

    return result


@mcp.tool()
def compare_weather(city1: str, city2: str) -> str:
    """
    比较两个城市的天气.

    :param city1: 第一个城市
    :param city2: 第二个城市
    """
    weather1 = generate_current_weather(city1)
    weather2 = generate_current_weather(city2)

    temp_diff = weather1["temperature"] - weather2["temperature"]

    result = f"🌍 Weather Comparison\n\n"
    result += f"   {weather1['city']} vs {weather2['city']}\n\n"

    result += f"   {weather1['icon']} {weather1['city']}:\n"
    result += f"      温度：{weather1['temperature']}°C | {weather1['condition']}\n"
    result += f"      湿度：{weather1['humidity']}% | 风速：{weather1['wind_speed']} km/h\n\n"

    result += f"   {weather2['icon']} {weather2['city']}:\n"
    result += f"      温度：{weather2['temperature']}°C | {weather2['condition']}\n"
    result += f"      湿度：{weather2['humidity']}% | 风速：{weather2['wind_speed']} km/h\n\n"

    if temp_diff > 0:
        result += f"   📊 {weather1['city']} 比 {weather2['city']} 高 {temp_diff}°C\n"
    elif temp_diff < 0:
        result += f"   📊 {weather2['city']} 比 {weather1['city']} 高 {-temp_diff}°C\n"
    else:
        result += f"   📊 两地温度相同\n"

    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
