from app.agents.base import BaseAgent
from typing import List, Dict, Any

class SpecAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="Senior Technical Architect",
            goal="Create a detailed technical specification from user stories."
        )

    async def run(self, stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = f"""
        User Stories: {stories}
        
        Generate a comprehensive Technical Specification.
        Must include structured sections:
        - API contracts (OpenAPI snippets)
        - Data model/schema changes (Mermaid ER diagram)
        - Security considerations
        - Error handling strategy
        - Observability/logging plan
        - Test plan mapping acceptance criteria to tests
        - Implementation plan (files/modules to create or modify)
        - Spec sequence diagram (Mermaid)
        
        Respond in JSON format.
        """
        result = await self.chat(prompt, response_format="json_object")
        return result
