from fastmcp import FastMCP

# Create an MCP server named "ChinaFlights"
mcp = FastMCP("ChinaFlights")


@mcp.tool()
def search_flights(origin: str, destination: str, date: str) -> str:
    """
    搜索国内航班.
    :param origin: 出发城市名称（如 北京、上海、广州）
    :param destination: 目的地城市名称（如 成都、西安、杭州）
    :param date: 出发日期，格式 YYYY-MM-DD
    """
    # 模拟国内航班数据
    airlines = ["中国国航", "南方航空", "东方航空", "四川航空", "成都航空"]

    # 根据航线生成不同的航班号和价格
    flight_prices = {
        ("北京", "成都"): [1200, 1500],
        ("上海", "成都"): [1000, 1300],
        ("广州", "成都"): [800, 1100],
        ("深圳", "成都"): [900, 1200],
        ("杭州", "成都"): [700, 1000],
        ("南京", "成都"): [800, 1100],
        ("西安", "成都"): [400, 600],
        ("重庆", "成都"): [300, 500],
        ("武汉", "成都"): [600, 800],
        ("长沙", "成都"): [500, 700],
    }

    # 默认价格
    default_price = [600, 900]

    # 获取价格范围
    price_range = flight_prices.get((origin, destination), default_price)

    flights = [
        {
            "flight_id": f"{random_airline(origin, destination)}{random.randint(1000, 9999)}",
            "airline": random.choice(airlines),
            "origin": origin,
            "destination": destination,
            "departure": f"{date} 07:30",
            "arrival": f"{date} {get_arrival_time(origin, destination)}",
            "price": f"{price_range[0]} 元",
            "status": "可预订"
        },
        {
            "flight_id": f"{random_airline(origin, destination)}{random.randint(1000, 9999)}",
            "airline": random.choice(airlines),
            "origin": origin,
            "destination": destination,
            "departure": f"{date} 12:15",
            "arrival": f"{date} {get_arrival_time(origin, destination, 5)}",
            "price": f"{price_range[1]} 元",
            "status": "可预订"
        },
        {
            "flight_id": f"{random_airline(origin, destination)}{random.randint(1000, 9999)}",
            "airline": random.choice(airlines),
            "origin": origin,
            "destination": destination,
            "departure": f"{date} 18:45",
            "arrival": f"{date} {get_arrival_time(origin, destination, 3)}",
            "price": f"{int((price_range[0] + price_range[1]) / 2)} 元",
            "status": "可预订"
        }
    ]

    result = f"查询到 {len(flights)} 个从 {origin} 到 {destination} 的航班（{date}）:\n\n"
    for f in flights:
        result += f"✈️ {f['airline']} {f['flight_id']}\n"
        result += f"   {f['departure']} → {f['arrival']}\n"
        result += f"   价格：{f['price']} | 状态：{f['status']}\n\n"

    return result


def random_airline(origin, destination) -> str:
    """生成航空公司二字代码."""
    codes = ["CA", "CZ", "MU", "3U", "EU", "HU", "SC", "FM"]
    return random.choice(codes)


def get_arrival_time(origin, destination, hour_offset=0) -> str:
    """根据出发地和目的地估算到达时间."""
    # 简单模拟：默认 2-3 小时航程
    base_hours = [9, 10, 11, 14, 15, 20, 21]
    hour = base_hours[hash(origin + destination) % len(base_hours)] + hour_offset
    minute = random.choice(["00", "15", "30", "45"])
    return f"{hour:02d}:{minute}"


@mcp.tool()
def book_flight(flight_id: str, passenger_name: str, phone: str) -> str:
    """
    预订航班.
    :param flight_id: 航班号（如 CA1234）
    :param passenger_name: 乘机人姓名
    :param phone: 联系电话
    """
    confirmation_num = f"CN{flight_id}-{random.randint(1000, 9999)}"

    return (
        f"✅ 航班预订成功！\n"
        f"   确认号：{confirmation_num}\n"
        f"   航班号：{flight_id}\n"
        f"   乘机人：{passenger_name}\n"
        f"   联系电话：{phone}\n\n"
        f"请携带有效身份证件提前 2 小时到达机场办理值机手续."
    )


@mcp.tool()
def get_flight_status(flight_id: str, date: str) -> str:
    """
    查询航班状态.
    :param flight_id: 航班号
    :param date: 查询日期，格式 YYYY-MM-DD
    """
    statuses = ["准点", "延误", "取消", "已起飞", "计划"]
    status = random.choice(statuses)

    return (
        f"📋 航班 {flight_id}（{date}）状态：{status}\n"
        f"   如需更多信息，请联系航空公司客服."
    )


import random

if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run(transport="stdio")
