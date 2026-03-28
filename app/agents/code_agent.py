from app.agents.base import BaseAgent
from typing import List, Dict, Any
import json

class CodeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="Lead Software Engineer",
            goal="Implement the codebase based on the Technical Specification."
        )

    async def run(self, spec: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate production-ready code from technical specification.
        """
        prompt = f"""
        Technical Specification: {json.dumps(spec, indent=2)[:2000]}
        
        Generate the complete Python FastAPI backend code for the application.
        
        Requirements:
        - Use FastAPI framework
        - Follow clean architecture (models, routes, services, schemas)
        - Include Pydantic v2 models with validation
        - Add SQLAlchemy ORM models
        - Create unit tests with pytest
        - Include type hints on all functions
        - Add docstrings for all public functions
        - Use async/await patterns
        - Implement proper error handling
        
        Output structure:
        - app/models/
        - app/routes/
        - app/services/
        - app/schemas/
        - tests/
        - requirements.txt
        - conftest.py
        
        Respond in JSON format with key 'files' where each file path maps to content.
        Example: {{"files": {{"app/models/user.py": "...", "tests/test_user.py": "..."}}}}
        """
        
        try:
            result = await self.chat(prompt, response_format="json_object")
            files = result.get("files", {}) if isinstance(result, dict) else {}
            return files
        except Exception as e:
            # Return minimal structure on error
            return {
                "app/__init__.py": "# Generated code structure",
                "tests/__init__.py": "# Tests"
            }
    
    async def fix_code(
        self,
        spec: Dict[str, Any],
        original_code: Dict[str, str],
        errors: List[str]
    ) -> Dict[str, str]:
        """
        Regenerate specific code files based on validation errors.
        """
        error_summary = "\n".join(errors[:5])  # Top 5 errors
        
        prompt = f"""
        Technical Specification: {json.dumps(spec, indent=2)[:1000]}
        
        Original Code Files:
        {json.dumps(list(original_code.keys()))}
        
        Validation Errors Encountered:
        {error_summary}
        
        Please fix ONLY the files that are causing these errors.
        
        Keep all other files from the original code unchanged.
        Only return the files that need to be fixed.
        
        Respond in JSON format: {{"files": {{"app/path/file.py": "...fixed content..."}}}}
        """
        
        try:
            result = await self.chat(prompt, response_format="json_object")
            fixed_files = result.get("files", {}) if isinstance(result, dict) else {}
            
            # Merge fixed files with original
            merged = original_code.copy()
            merged.update(fixed_files)
            
            return merged
        except Exception as e:
            return original_code  # Return original on error

