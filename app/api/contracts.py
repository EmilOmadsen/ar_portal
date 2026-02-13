from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import traceback
import tempfile
import os

from app.core.contracts.loader import load_template
from app.core.contracts.builder.builder import build_context
from app.core.contracts.exporter import render_contract
from app.core.pdf_converter import docx_to_preview_images

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

@router.get("/templates")
async def list_templates():
    """List available contract templates"""
    try:
        templates_dir = Path(__file__).parent.parent.parent / "static" / "contract_templates"
        print(f"Looking for templates in: {templates_dir}")
        
        if not templates_dir.exists():
            return {"templates": [], "error": f"Directory not found: {templates_dir}"}
        
        # Only show the main template
        templates = ["50_50 template med placeholders.docx"]
        print(f"Templates available: {templates}")
        
        return {"templates": templates}
    except Exception as e:
        print(f"Error listing templates: {e}")
        import traceback
        traceback.print_exc()
        return {"templates": [], "error": str(e)}

@router.post("/generate")
async def generate_contract(payload: dict):
    """Generate a contract from template and data"""
    try:
        print(f"=== Generating Contract ===")
        print(f"Payload: {payload}")
        
        template = load_template(payload.get("template_name"))
        print(f"Template loaded successfully")
        
        context = build_context(payload)
        print(f"Context built: {context}")
        
        output_path = render_contract(template, context)
        print(f"Contract rendered to: {output_path}")

        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="contract_generated.docx"
        )
    except Exception as e:
        print(f"ERROR generating contract: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview")
async def preview_contract(payload: dict):
    """Generate contract preview as PDF images"""
    try:
        print(f"=== Generating Contract Preview ===")
        print(f"Payload: {payload}")
        
        # Generate contract
        template = load_template(payload.get("template_name"))
        context = build_context(payload)
        output_path = render_contract(template, context)
        print(f"Contract generated: {output_path}")
        
        # Convert to PDF images
        print(f"Converting to PDF images...")
        images = docx_to_preview_images(output_path, dpi=150)
        print(f"Generated {len(images)} preview images")
        
        # Clean up the DOCX file
        try:
            os.remove(output_path)
        except:
            pass
        
        return {
            "success": True,
            "pages": len(images),
            "images": images
        }
        
    except Exception as e:
        print(f"ERROR generating preview: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating contract: {str(e)}")
