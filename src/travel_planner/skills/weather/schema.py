"""Weather Skill Schema - Input/Output definitions."""

from pydantic import BaseModel, Field


class WeatherInput(BaseModel):
    """Input schema for weather skill.

    Attributes:
        city: 城市名称（如"成都"、"苏州"）
        province: 省份名称（如"四川省"、"江苏省"），可选
    """
    city: str = Field(..., description="城市名称，如'成都'、'苏州'")
    province: str  = Field(..., description="省份名称，如'四川省'、'江苏省'")


class WeatherOutput(BaseModel):
    """Output schema for weather skill.

    Attributes:
        city: 完整城市名称
        temp: 实时温度（摄氏度）
        condition: 天气状况（晴、雨、多云等）
        humidity: 湿度百分比
        wind_level: 风力等级
        aqi: 空气质量指数（可选）
        forecast: 天气预报摘要（可选）
        success: 是否成功获取数据
        error: 错误信息（如果有）
    """
    city: str = Field(..., description="完整城市名称")
    time: str = Field(..., description="当前时间")
    temp: float | None = Field(None, description="实时温度（摄氏度）")
    condition: str | None = Field(None, description="天气状况")
    humidity: int | None = Field(None, description="湿度百分比")
    wind_level: str | None = Field(None, description="风力等级")
    aqi: int | None = Field(None, description="空气质量指数")
    forecast: list | None = Field(None, description="天气预报摘要")
    success: bool = Field(True, description="是否成功获取数据")
    error: str | None = Field(None, description="错误信息")
