"""MCP Hotel Server - 酒店搜索服务."""

from fastmcp import FastMCP
import random
from datetime import date, timedelta

# 创建 MCP 服务器
mcp = FastMCP("HotelSearch")


# 模拟酒店品牌
HOTEL_CHAINS = [
    "希尔顿", "万豪", "假日酒店", "如家", "华住",
    "亚朵", "全季", "汉庭", "锦江", "格林豪泰"
]

# 中国城市列表
CITY_NAMES = {
    "成都": "成都", "北京": "北京", "上海": "上海",
    "广州": "广州", "深圳": "深圳", "杭州": "杭州",
    "西安": "西安", "南京": "南京", "重庆": "重庆",
    "武汉": "武汉", "长沙": "长沙", "厦门": "厦门",
    "青岛": "青岛", "大理": "大理", "丽江": "丽江"
}


def generate_hotels(
    city: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    rooms: int = 1
) -> list[dict]:
    """生成模拟酒店列表."""
    # 获取城市名称
    city_name = CITY_NAMES.get(city, city)

    hotels = []
    base_price = random.randint(200, 800)

    # 计算入住天数
    try:
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)
        nights = (check_out_date - check_in_date).days
        if nights <= 0:
            nights = 1
    except Exception:
        nights = 1

    # 成都特色地点
    chengdu_landmarks = ["春熙路", "太古里", "宽窄巷子", "锦里", "天府广场", "成都东站", "双流机场"]

    for i in range(random.randint(5, 10)):
        chain = random.choice(HOTEL_CHAINS)
        if city == "成都" or "成都" in city:
            location = random.choice(chengdu_landmarks)
        else:
            location = random.choice(["市中心", "机场附近", "火车站", "景区", "商业区", "大学城"])

        hotels.append({
            "hotel_id": f"HTL{random.randint(10000, 99999)}",
            "name": f"{chain}酒店 ({city_name}{location}店)",
            "chain": chain,
            "address": f"{city_name}{random.choice(['区', '县'])}{random.randint(1, 999)}号",
            "stars": random.randint(3, 5),
            "price_per_night": base_price + i * 50,
            "total_price": (base_price + i * 50) * nights,
            "currency": "CNY",
            "nights": nights,
            "rooms_available": rooms,
            "amenities": random.sample(
                ["wifi", "停车场", "健身房", "餐厅", "会议室", "洗衣服务", "接送机", "早餐"],
                k=random.randint(3, 7)
            ),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "review_count": random.randint(100, 5000),
            "cancellation": random.choice(["免费取消", "限时取消", "不可取消"]),
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

    :param city: 城市名称 (如 成都，北京，上海)
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
        return f"未找到符合条件的酒店."

    # 格式化输出
    result = f"在 {city} 找到 {len(hotels)} 家酒店:\n\n"

    for h in hotels[:8]:  # 最多显示 8 个
        result += f"🏨 {h['name']}\n"
        result += f"   ⭐ {h['stars']}星级 | 评分：{h['rating']} ({h['review_count']}条评价)\n"
        result += f"   📍 {h['address']}\n"
        result += f"   💰 ¥{h['price_per_night']}/晚 | 总计：¥{h['total_price']} ({h['nights']}晚)\n"
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
        "name": f"酒店 {hotel_id}",
        "description": "位于市中心的舒适酒店.",
        "check_in_time": "15:00",
        "check_out_time": "11:00",
        "policies": [
            "房间内禁止吸烟",
            "允许携带宠物（需额外收费）",
            "12 岁以下儿童免费"
        ]
    }

    result = f"📋 酒店详情 {base_hotel['hotel_id']}:\n"
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
        f"✅ 酒店预订确认！\n"
        f"   确认号：{confirmation_num}\n"
        f"   酒店 ID: {hotel_id}\n"
        f"   入住人：{guest_name}\n"
        f"   入住日期：{check_in}\n"
        f"   退房日期：{check_out}\n\n"
        f"请携带确认号和有效身份证件办理入住."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
