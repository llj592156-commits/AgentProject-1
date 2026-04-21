---
id: skill_weather
name: 天气查询
description: 根据城市名称查询实时天气与预报信息
version: 1.0.0
author: travel_planner_team
tags: [tool, api, weather, travel]
input_schema: schema.WeatherInput
output_schema: schema.WeatherOutput
model: qwen3.5-plus
timeout: 15
retry: 2
is_public: true
---

# 天气查询 Skill

## 功能描述
根据用户提供的目的地城市名称，调用天气 API 获取实时天气信息，包括：
- 实时温度
- 天气状况（晴、雨、多云等）
- 湿度
- 风力等级
- 空气质量指数

## 调用示例
**输入：**
```json
{"city": "成都", "province": "四川省"}
```

**输出：**
```json
{
  "city": "四川省成都市",
  "temp": 25.5,
  "condition": "晴天",
  "humidity": 60,
  "wind_level": "微风",
  "aqi": 45,
  "forecast": "未来三天天气良好，适合出行"
}
```

## 业务规则
1. 支持省份 + 城市格式（如"四川省成都市"）或单独城市名
2. 城市名称支持中文、拼音
3. API 调用失败时返回友好提示
4. 无数据时返回 `success: false` 并说明原因

## 依赖
- 外部 API: 墨迹天气 API (t.weather.itboy.net)
- 城市代码映射：area_code.json
- 环境变量：无

## 错误处理
| 错误类型 | 返回消息 |
|---------|---------|
| 城市代码未找到 | "未找到该城市的天气数据" |
| API 调用失败 | "天气服务暂时不可用" |
| API 返回非 200 状态 | "天气数据获取失败" |
