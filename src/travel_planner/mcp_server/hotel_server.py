"""MCP Hotel Server - 酒店搜索服务."""

from fastmcp import FastMCP
import random
from datetime import date, timedelta

# 创建 MCP 服务器
mcp = FastMCP("HotelSearch")


# 模拟酒店数据
HOTEL_CHAINS = [
    "Hilton", "Marriott", "Holiday Inn", "Ibis", "Mercure",
    "Novotel", "Radisson", "Sheraton", "Westin", "Hyatt"
]

CITY_NAMES = {
    "PAR": "Paris", "IST": "Istanbul", "LON": "London",
    "NYC": "New York", "TYO": "Tokyo", "BER": "Berlin",
    "ROM": "Rome", "MAD": "Madrid", "AMS": "Amsterdam"
}


def generate_hotels(
    city: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    rooms: int = 1
) -> list[dict]:
    """生成模拟酒店列表."""
    # 解析城市代码
    city_name = CITY_NAMES.get(city.upper(), city)

    hotels = []
    base_price = random.randint(80, 400)

    # 计算入住天数
    try:
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)
        nights = (check_out_date - check_in_date).days
        if nights <= 0:
            nights = 1
    except Exception:
        nights = 1

    for i in range(random.randint(5, 10)):
        chain = random.choice(HOTEL_CHAINS)
        location = random.choice([
            "City Center", "Airport", "Train Station",
            "Beach Front", "Old Town", "Business District"
        ])

        hotels.append({
            "hotel_id": f"HTL{random.randint(10000, 99999)}",
            "name": f"{chain} {city_name} {location}",
            "chain": chain,
            "address": f"{random.randint(1, 999)} {random.choice(['Main', 'First', 'Second', 'Park'])} Street",
            "stars": random.randint(3, 5),
            "price_per_night": base_price + i * 25,
            "total_price": (base_price + i * 25) * nights,
            "currency": "EUR",
            "nights": nights,
            "rooms_available": rooms,
            "amenities": random.sample(
                ["wifi", "pool", "gym", "parking", "restaurant", "bar", "spa", "room_service", "concierge"],
                k=random.randint(3, 7)
            ),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "review_count": random.randint(100, 5000),
            "cancellation": random.choice(["free", "partial", "non-refundable"]),
        })

    return sorted(hotels, key=lambda x: x["price_per_night"])


@mcp.tool()
def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    rooms: int = 1,
    max_price: int | None = None,
    min_rating: float | None = None,
) -> str:
    """
    搜索指定城市的酒店.

    :param city: 城市名称或机场代码 (如 PAR, IST, LON)
    :param check_in: 入住日期，格式 YYYY-MM-DD
    :param check_out: 退房日期，格式 YYYY-MM-DD
    :param guests: 入住人数，默认 1
    :param rooms: 房间数量，默认 1
    :param max_price: 最高价格限制 (可选)
    :param min_rating: 最低评分要求 (可选)
    """
    hotels = generate_hotels(city, check_in, check_out, guests, rooms)

    # 应用过滤条件
    if max_price:
        hotels = [h for h in hotels if h["price_per_night"] <= max_price]
    if min_rating:
        hotels = [h for h in hotels if h["rating"] >= min_rating]

    if not hotels:
        return f"No hotels found matching your criteria."

    # 格式化输出
    result = f"Found {len(hotels)} hotels in {city}:\n\n"

    for h in hotels[:8]:  # 最多显示 8 个
        result += f"🏨 {h['name']}\n"
        result += f"   ⭐ {h['stars']}星级 | 评分：{h['rating']} ({h['review_count']}条评价)\n"
        result += f"   📍 {h['address']}\n"
        result += f"   💰 €{h['price_per_night']}/晚 | 总计：€{h['total_price']} ({h['nights']}晚)\n"
        result += f"   ✨ 设施：{', '.join(h['amenities'][:5])}\n"
        result += f"   📋 取消政策：{h['cancellation']}\n"
        result += f"   🔖 酒店 ID: {h['hotel_id']}\n\n"

    if len(hotels) > 8:
        result += f"... 还有 {len(hotels) - 8} 家酒店\n"

    return result


@mcp.tool()
def get_hotel_details(hotel_id: str) -> str:
    """
    获取酒店详细信息.

    :param hotel_id: 酒店 ID (如 HTL12345)
    """
    # 模拟生成酒店详情
    base_hotel = {
        "hotel_id": hotel_id,
        "name": f"Hotel {hotel_id}",
        "description": "A beautiful hotel in the heart of the city.",
        "check_in_time": "15:00",
        "check_out_time": "11:00",
        "policies": [
            "No smoking in rooms",
            "Pets allowed with extra charge",
            "Children under 12 stay free"
        ]
    }

    result = f"📋 Hotel Details for {base_hotel['hotel_id']}:\n"
    result += f"   {base_hotel['name']}\n"
    result += f"   {base_hotel['description']}\n\n"
    result += f"   ⏰ 入住时间：{base_hotel['check_in_time']}\n"
    result += f"   ⏰ 退房时间：{base_hotel['check_out_time']}\n\n"
    result += f"   📜 酒店政策:\n"
    for policy in base_hotel['policies']:
        result += f"      - {policy}\n"

    return result


@mcp.tool()
def book_hotel(
    hotel_id: str,
    guest_name: str,
    check_in: str,
    check_out: str,
) -> str:
    """
    预订酒店.

    :param hotel_id: 酒店 ID
    :param guest_name: 预订人姓名
    :param check_in: 入住日期
    :param check_out: 退房日期
    """
    confirmation_num = f"HTL-{hotel_id}-{random.randint(1000, 9999)}"

    return (
        f"✅ Hotel booking confirmed!\n"
        f"   确认号：{confirmation_num}\n"
        f"   酒店 ID: {hotel_id}\n"
        f"   入住人：{guest_name}\n"
        f"   入住日期：{check_in}\n"
        f"   退房日期：{check_out}\n\n"
        f"请携带确认号和有效身份证件办理入住."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
