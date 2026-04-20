"""Info Skill - Gathers travel-related information.

Provides:
- Weather forecasts
- Visa requirements
- Currency exchange
- Travel advisories
- Local information
"""

from travel_planner.skills.base_skill import BaseSkill, SkillContext, SkillResult
import requests
import os
import json
import re


class InfoSkill(BaseSkill):
    """Skill for gathering travel information."""

    @property
    def name(self) -> str:
        return "info"

    @property
    def description(self) -> str:
        return "Gather travel information like weather, visa requirements, and local tips."

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the info gathering skill."""
        self._log_execution("start", "Gathering travel information")

        area_code = None
        # Get area code if destination is known
        if context.state.travel_params and context.state.travel_params.destination:
            destination = context.state.travel_params.destination
            
            # province, city = destination.split("省"|"市")
            match = re.match(r"(.+?[省市])?(.+)", destination)
            if match:
                province = match.group(1).replace("省", "").replace("市", "") or ""  # # 如 "四川省" 或 "北京市"
                city = match.group(2).replace("市", "") or ""       # 如 "内江" 或 "朝阳"


            with open(r"D:\AgentProject\Project-1\langgraph-template-travel-planner\src\travel_planner\helpers\area_code.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                # Search through provinces and cities
                for provinces in data["城市代码"]:
                    # Check province name
                    if province in provinces["省"]:
                        # Get first city code as default
                        for citys in provinces["市"]:
                            if city in citys["市名"]:
                                area_code = citys["编码"]
                                break
                        if area_code:
                                break
                    
        if not area_code:
            return SkillResult.fail(
                message=f"Could not find area code for: {destination}",
                error=f"City '{destination}' not found in area_code.json",
            )

        url = f"http://t.weather.itboy.net/api/weather/city/{area_code}"
        response = requests.get(url)
        data = response.json()
        # print(data)
        if data["status"] == 200:
            weather = data["data"]
        else:
            weather = {"error": f"API returned status {data['status']}"}

        self._log_execution("complete", f"Gathered weather: {weather}")

        return SkillResult.ok(
            message="Travel information gathered",
            state_updates={"travel_info": weather},
            data=weather
        )


