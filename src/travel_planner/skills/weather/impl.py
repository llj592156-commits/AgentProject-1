"""Weather Skill Implementation - Pure function logic."""

import json
from pathlib import Path

import requests

from .schema import WeatherInput, WeatherOutput


def run(input_data: dict) -> dict:
    """Weather skill entry point.

    Args:
        input_data: Dictionary with 'city' and optional 'province' keys

    Returns:
        Dictionary with weather output data
    """
    parsed = WeatherInput(**input_data)
    output = _get_weather(parsed)
    return output.model_dump()


def _get_weather(input_data: WeatherInput) -> WeatherOutput:
    """Get weather data for the specified city.

    Args:
        input_data: Parsed weather input

    Returns:
        WeatherOutput with weather data or error message
    """
    area_code = _get_area_code(input_data.city, input_data.province)

    if not area_code:
        return WeatherOutput(
            city=f"{input_data.province or ''}{input_data.city}",
            success=False,
            error=f"未找到城市 '{input_data.city}' 的天气数据"
        )

    try:
        url = f"http://t.weather.itboy.net/api/weather/city/{area_code}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != 200:
            return WeatherOutput(
                city=f"{input_data.province or ''}{input_data.city}",
                success=False,
                error=f"天气 API 返回状态码：{data.get('status', 'unknown')}"
            )

        weather_data = data.get("data", {})
        city_info = data.get("cityInfo", {})
        forecast = weather_data.get("forecast", [])

        # 解析实时天气数据
        shidu = weather_data.get("shidu", "")
        humidity = None
        if shidu:
            try:
                humidity = int(shidu.replace("%", ""))
            except ValueError:
                pass

        wendu = weather_data.get("wendu", "")
        temp = None
        if wendu:
            try:
                temp = float(wendu)
            except ValueError:
                pass

        # 获取今天预报
        today_forecast = weather_data.get("forecast", [])
        today = today_forecast[0] if today_forecast else {}
        condition = today.get("type", "")
        wind_level = today.get("fl", "")

        return WeatherOutput(
            city=city_info.get("city", f"{input_data.province or ''}{input_data.city}"),
            time=data.get("time", ""),
            temp=temp,
            condition=condition,
            humidity=humidity,
            wind_level=wind_level,
            forecast=forecast,
            success=True
        )

    except requests.Timeout:
        return WeatherOutput(
            city=f"{input_data.province or ''}{input_data.city}",
            success=False,
            error="天气服务请求超时"
        )
    except requests.RequestException:
        return WeatherOutput(
            city=f"{input_data.province or ''}{input_data.city}",
            success=False,
            error="天气服务暂时不可用"
        )
    except Exception as e:
        return WeatherOutput(
            city=f"{input_data.province or ''}{input_data.city}",
            success=False,
            error=f"天气数据获取失败：{str(e)}"
        )


def _get_area_code(city: str, province: str | None = None) -> str | None:
    """Get area code for the specified city.

    Args:
        city: City name
        province: Province name (optional)

    Returns:
        Area code string or None if not found
    """
    # 确定 area_code.json 路径
    area_code_path = r"D:\AgentProject\Project-1\langgraph-template-travel-planner\src\travel_planner\helpers\area_code.json"

    if not Path(area_code_path).exists():
        return None

    with open(area_code_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 标准化输入
    city_clean = city.replace("市", "")
    province_clean = (province or "").replace("省", "").replace("市", "")

    # 遍历城市代码数据
    for province_entry in data.get("城市代码", []):
        province_name = province_entry.get("省", "")

        # 如果指定了省份，先匹配省份
        if province_clean and province_clean not in province_name:
            continue

        # 遍历该省的城市
        for city_entry in province_entry.get("市", []):
            city_name = city_entry.get("市名", "").replace("市", "")

            if city_clean in city_name or city_name in city_clean:
                return city_entry.get("编码")

    return None

if __name__ == "__main__":
    weather = run({"city": "成都", "province": "四川省"})
    print(weather)