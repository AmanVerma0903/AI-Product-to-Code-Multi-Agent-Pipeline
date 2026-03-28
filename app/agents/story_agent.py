from app.agents.base import BaseAgent
from typing import List, Dict, Any

class StoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="Product Owner",
            goal="Decompose Epics into detailed User Stories."
        )

    async def run(self, epics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        prompt = f"""
        Epics: {epics}
        
        Generate User Stories for these epics.
        Include non-functional requirements (performance, security, privacy).
        Each story should have: 
        - Title
        - Description
        - Acceptance Criteria
        - Priority
        - Story Points / Estimates
        - Estimate Rationale
        - Edge Cases to consider
        
        Respond in JSON format with a key 'stories' (list).


        """
        result = await self.chat(prompt, response_format="json_object")
        return result
