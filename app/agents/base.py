from openai import AsyncOpenAI
from app.core.config import settings
import json

class BaseAgent:
    def __init__(self, role: str, goal: str):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.role = role
        self.goal = goal

    async def chat(self, prompt: str, system_message: str = None, response_format: str = "text"):
        if not system_message:
            system_message = f"You are a {self.role}. Your goal is {self.goal}."
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        response_args = {
            "model": "gpt-4.1",
            "messages": messages,
        }
        
        if response_format == "json_object":
            response_args["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**response_args)
        content = response.choices[0].message.content
        
        if response_format == "json_object":
            return json.loads(content)
        return content
