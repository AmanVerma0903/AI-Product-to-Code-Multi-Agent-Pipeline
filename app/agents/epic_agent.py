from app.agents.base import BaseAgent
from typing import List, Dict, Any

class EpicAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="Product Manager / Architect",
            goal="Transform requirements and research into high-level Epics."
        )

    async def run(self, requirement: str, research_summary: str) -> List[Dict[str, Any]]:
        prompt = f"""
        Requirement: {requirement}
        Research Summary: {research_summary}
        
        Generate a set of Epics for this project. 
        Each Epic should have a title, description, and dependency list.
        Include a Mermaid diagram (dependency diagram).
        
        Respond in JSON format with a key 'epics' (list) and 'mermaid_diagram' (string).
        """
        result = await self.chat(prompt, response_format="json_object")
        return result
