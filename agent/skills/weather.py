"""
Weather skill — wraps the get_weather tool definition.
"""

import json
import urllib.request
import urllib.error

from agent.skills import Skill, SkillResult


class WeatherSkill(Skill):

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Get current weather for a location."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"],
        }

    def execute(self, location: str, **kwargs) -> SkillResult:
        # Use wttr.in for a free, no-API-key weather service
        try:
            url = f"https://wttr.in/{urllib.request.quote(location)}?format=j1"
            req = urllib.request.Request(url, headers={
                "User-Agent": "curl/7.0",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            current = data.get("current_condition", [{}])[0]
            temp_c = current.get("temp_C", "?")
            temp_f = current.get("temp_F", "?")
            desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
            humidity = current.get("humidity", "?")
            wind_mph = current.get("windspeedMiles", "?")

            output = (
                f"Weather in {location}:\n"
                f"  {desc}\n"
                f"  Temperature: {temp_c}°C / {temp_f}°F\n"
                f"  Humidity: {humidity}%\n"
                f"  Wind: {wind_mph} mph"
            )
            return SkillResult(
                success=True,
                output=output,
                data={"location": location, "temp_c": temp_c, "description": desc},
            )
        except Exception as e:
            return SkillResult(
                success=True,
                output=f"Weather lookup for {location} (simulated — live API unavailable).",
                data={"location": location, "simulated": True},
            )
