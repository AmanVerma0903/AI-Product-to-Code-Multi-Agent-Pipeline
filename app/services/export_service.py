import zipfile
import io
import json
from typing import Dict, List, Any
from datetime import datetime
import fitz  # PyMuPDF


class ExportService:
    @staticmethod
    def create_code_bundle(files: Dict[str, str]) -> io.BytesIO:
        """Create a ZIP bundle of generated code files."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path, content in files.items():
                if isinstance(content, str):
                    zip_file.writestr(file_path, content)
        zip_buffer.seek(0)
        return zip_buffer

    @staticmethod
    def format_markdown(artifact_type: str, content: Dict) -> str:
        """Convert artifact JSON to markdown format."""
        md = f"# {artifact_type.capitalize()} Artifact\n\n"
        md += f"*Generated: {datetime.now().isoformat()}*\n\n"

        if isinstance(content, dict):
            for key, value in content.items():
                heading = key.replace('_', ' ').capitalize()
                md += f"## {heading}\n\n"

                if isinstance(value, list):
                    for item in value:
                        md += f"- {json.dumps(item, indent=2) if isinstance(item, dict) else str(item)}\n"
                elif isinstance(value, dict):
                    md += f"```json\n{json.dumps(value, indent=2)}\n```\n"
                else:
                    md += f"{str(value)}\n"

                md += "\n"
        else:
            md += str(content)

        return md

    @staticmethod
    def create_pdf_report(title: str, artifacts: List[Dict[str, Any]]) -> io.BytesIO:
        """Generate PDF report from artifacts."""
        pdf_buffer = io.BytesIO()
        doc = fitz.open()

        page = doc.new_page()
        page.insert_text((50, 50), title, fontsize=28)
        page.insert_text(
            (50, 100),
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            fontsize=10,
        )

        for artifact in artifacts:
            artifact_type = artifact.get("type", "Unknown")
            content = artifact.get("content", {})

            page = doc.new_page()
            y_pos = 50
            page.insert_text((50, y_pos), f"{artifact_type}", fontsize=16)
            y_pos += 40

            if isinstance(content, dict):
                for key, value in content.items():
                    page.insert_text((70, y_pos), key.replace('_', ' ').title(), fontsize=12)
                    y_pos += 20

                    text = json.dumps(value, indent=2) if not isinstance(value, str) else value
                    for line in text.split("\n")[:20]:
                        page.insert_text((90, y_pos), line[:100], fontsize=9)
                        y_pos += 12
                        if y_pos > 750:
                            page = doc.new_page()
                            y_pos = 50

        doc.save(pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer

    @staticmethod
    def create_full_report(run_data: Dict[str, Any], artifacts: List[Dict[str, Any]]) -> io.BytesIO:
        """Create ZIP containing all artifacts + generated code files."""
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

            # Metadata
            metadata = {
                "run_id": run_data.get("id"),
                "project_id": run_data.get("project_id"),
                "status": run_data.get("status"),
                "generated_at": datetime.now().isoformat(),
                "artifacts": len(artifacts),
            }
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))

            # Process artifacts
            for idx, artifact in enumerate(artifacts):
                artifact_type = artifact.get("type", "unknown")
                content = artifact.get("content", {})

                # Save JSON + Markdown
                zip_file.writestr(f"{idx}_{artifact_type}.json", json.dumps(content, indent=2))
                zip_file.writestr(f"{idx}_{artifact_type}.md", ExportService.format_markdown(artifact_type, content))

                #   FIXED PART — CODE FILE EXPORT
                if artifact_type == "Code" and isinstance(content, dict):
                    for file_path, file_content in content.items():
                        if isinstance(file_content, str):
                            zip_file.writestr(f"generated_code/{file_path}", file_content)

        zip_buffer.seek(0)
        return zip_buffer