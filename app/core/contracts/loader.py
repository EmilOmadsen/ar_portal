import os
from pathlib import Path
from docxtpl import DocxTemplate

def load_template(filename="50_50 template med placeholders.docx"):
    # Get absolute path from this file's location
    base_dir = Path(__file__).parent.parent.parent.parent
    template_path = base_dir / "static" / "contract_templates" / filename
    return DocxTemplate(str(template_path))
