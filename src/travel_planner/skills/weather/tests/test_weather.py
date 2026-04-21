"""Tests for Weather Skill."""

import pytest

from .impl import run, _get_area_code
from .schema import WeatherInput, WeatherOutput


class TestWeatherInput:
    """Test cases for WeatherInput schema."""

    def test_valid_input_with_city_only(self):
        """Test input with only city name."""
        input_data = WeatherInput(city="成都")
        assert input_data.city == "成都"
        assert input_data.province is None

    def test_valid_input_with_province(self):
        """Test input with city and province."""
        input_data = WeatherInput(city="成都", province="四川省")
        assert input_data.city == "成都"
        assert input_data.province == "四川省"


class TestWeatherOutput:
    """Test cases for WeatherOutput schema."""

    def test_success_output(self):
        """Test successful weather output."""
        output = WeatherOutput(
            city="四川省成都市",
            temp=25.5,
            condition="晴天",
            humidity=60,
            success=True
        )
        assert output.success is True
        assert output.temp == 25.5
        assert output.error is None

    def test_error_output(self):
        """Test error weather output."""
        output = WeatherOutput(
            city="未知城市",
            success=False,
            error="未找到该城市的天气数据"
        )
        assert output.success is False
        assert output.error is not None


class TestRun:
    """Test cases for run function."""

    def test_run_with_valid_city(self):
        """Test run function with a valid city."""
        # 使用苏州作为测试城市（area_code.json 中应该存在）
        result = run({"city": "苏州", "province": "江苏省"})
        assert isinstance(result, dict)
        assert "city" in result
        assert "success" in result

    def test_run_with_invalid_city(self):
        """Test run function with an invalid city."""
        result = run({"city": "无效城市 XYZ", "province": "无效省份"})
        assert result["success"] is False
        assert "error" in result


class TestGetAreaCode:
    """Test cases for _get_area_code function."""

    def test_find_city_with_province(self):
        """Test finding city code with province specified."""
        code = _get_area_code("苏州", "江苏省")
        assert code is not None

    def test_find_city_without_province(self):
        """Test finding city code without province."""
        code = _get_area_code("北京")
        assert code is not None

    def test_city_not_found(self):
        """Test when city is not found."""
        code = _get_area_code("无效城市 XYZ")
        assert code is None
