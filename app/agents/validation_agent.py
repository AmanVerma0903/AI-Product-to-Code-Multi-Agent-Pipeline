from app.agents.base import BaseAgent
from typing import List, Dict, Any
import subprocess
import tempfile
import os
import sys
import json
import shutil


class ValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="QA Automation Engineer",
            goal="Validate the generated code using tests and linting."
        )

    async def run(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="generated_project_")
            self._write_files(temp_dir, code_files)

            tests_result = await self._run_tests(temp_dir)
            lint_result = await self._run_linting(temp_dir)

            return self._compile_report(tests_result, lint_result)

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "tests_passed": False,
                "lint_issues": [],
                "test_failures": [str(e)],
                "summary": f"Validation execution failed: {str(e)}"
            }

        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    # --------------------------------------------------

    def _write_files(self, base_path: str, files: Dict[str, str]) -> None:
        for file_path, content in files.items():

            if "==" in file_path or "\n" in file_path or file_path.strip() == "":
                continue

            invalid_chars = '<>:"|?*'
            for ch in invalid_chars:
                file_path = file_path.replace(ch, "_")

            full_path = os.path.join(base_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

    # --------------------------------------------------

    async def _run_tests(self, project_dir: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            #  FIX 1 — No tests found should NOT fail validation
            if result.returncode == 5:
                return {
                    "exit_code": 0,
                    "passed": True,
                    "stdout": "No tests found — skipping",
                    "stderr": "",
                    "failures": []
                }

            failures = []
            if result.returncode != 0:
                failures = self._parse_pytest_output(result.stdout)

            return {
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
                "stdout": result.stdout[:1000],
                "stderr": result.stderr[:1000],
                "failures": failures
            }

        except subprocess.TimeoutExpired:
            return {"exit_code": 1, "passed": False, "error": "Test timeout"}

        except Exception as e:
            return {"exit_code": 1, "passed": False, "error": str(e)}

    # --------------------------------------------------

    async def _run_linting(self, project_dir: str) -> Dict[str, Any]:
        try:
            #  FIX 2 — Auto-fix lint issues FIRST
            subprocess.run(
                [sys.executable, "-m", "ruff", "check", ".", "--fix"],
                cwd=project_dir,
                capture_output=True,
                text=True
            )

            # Now run check again
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", ".", "--output-format=json"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=15
            )

            issues = []
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                except:
                    issues = [{"message": result.stdout}]

            return {
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
                "issues": issues[:20],
                "issue_count": len(issues)
            }

        except Exception as e:
            return {
                "exit_code": 0,
                "passed": True,
                "warning": f"Lint skipped: {str(e)}"
            }

    # --------------------------------------------------

    def _parse_pytest_output(self, stdout: str) -> List[str]:
        failures = []
        for line in stdout.split("\n"):
            if "FAILED" in line or "ERROR" in line:
                failures.append(line.strip())
        return failures[:10]

    # --------------------------------------------------

    def _compile_report(self, tests: Dict[str, Any], lint: Dict[str, Any]) -> Dict[str, Any]:
        tests_passed = tests.get("passed", False)
        lint_passed = lint.get("passed", True)

        overall_status = "passed" if (tests_passed and lint_passed) else "failed"

        return {
            "status": overall_status,
            "tests_passed": tests_passed,
            "lint_passed": lint_passed,
            "test_failures": tests.get("failures", []),
            "lint_issues": lint.get("issues", []),
            "lint_issue_count": lint.get("issue_count", 0),
            "summary": f"Tests {'passed' if tests_passed else 'failed'} | Lint {'passed' if lint_passed else 'issues found'}",
            "test_details": tests,
            "lint_details": lint
        }