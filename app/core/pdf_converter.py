"""
PDF conversion utilities for contract preview
Converts DOCX to PDF and then to images for live preview
"""
import os
import tempfile
import base64
from pathlib import Path
from typing import List
import subprocess
import sys
import platform

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    from PIL import Image
except ImportError:
    Image = None


def find_poppler_path():
    """Find Poppler installation path (required for pdf2image on Windows)"""
    if platform.system() == 'Windows':
        # Check common installation paths
        common_paths = [
            r"C:\Program Files\poppler\Library\bin",
            r"C:\Program Files (x86)\poppler\Library\bin",
            os.path.join(os.path.expanduser("~"), "AppData", "Local", "poppler", "Library", "bin"),
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
    return None


def docx_to_pdf(docx_path: str) -> str:
    """
    Convert DOCX file to PDF using LibreOffice
    
    Args:
        docx_path: Path to the .docx file
        
    Returns:
        Path to the generated PDF file
    """
    # Create temp directory for output
    temp_dir = tempfile.gettempdir()
    
    # Try LibreOffice on Windows first
    if platform.system() == 'Windows':
        # Try common LibreOffice paths
        libreoffice_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        
        for soffice in libreoffice_paths:
            if os.path.exists(soffice):
                try:
                    subprocess.run([
                        soffice,
                        '--headless',
                        '--convert-to', 'pdf',
                        '--outdir', temp_dir,
                        docx_path
                    ], check=True, capture_output=True, timeout=30)
                    
                    pdf_filename = Path(docx_path).stem + '.pdf'
                    pdf_path = os.path.join(temp_dir, pdf_filename)
                    
                    if os.path.exists(pdf_path):
                        return pdf_path
                except Exception as e:
                    print(f"LibreOffice conversion failed with {soffice}: {e}")
                    continue
    else:
        # Try libreoffice on Unix/Linux/Mac
        try:
            subprocess.run([
                'libreoffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', temp_dir,
                docx_path
            ], check=True, capture_output=True, timeout=30)
            
            pdf_filename = Path(docx_path).stem + '.pdf'
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            if os.path.exists(pdf_path):
                return pdf_path
        except Exception as e:
            print(f"LibreOffice conversion failed: {e}")
    
    raise Exception("LibreOffice not available for PDF conversion. Please install LibreOffice.")


def pdf_to_images_base64(pdf_path: str, dpi: int = 200) -> List[str]:
    """
    Convert PDF to images and return as base64 strings
    
    Args:
        pdf_path: Path to the PDF file
        dpi: DPI for image conversion (higher = better quality but larger)
        
    Returns:
        List of base64-encoded image strings (one per page)
    """
    if not PDF2IMAGE_AVAILABLE:
        raise Exception("pdf2image not installed. Install with: pip install pdf2image")
    
    try:
        # Find Poppler on Windows
        poppler_path = find_poppler_path()
        kwargs = {}
        if poppler_path:
            kwargs['poppler_path'] = poppler_path
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=dpi, **kwargs)
        
        # Convert images to base64
        base64_images = []
        for image in images:
            # Save to bytes
            import io
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Encode to base64
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            base64_images.append(f"data:image/png;base64,{img_base64}")
        
        return base64_images
        
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        raise


def docx_to_preview_images(docx_path: str, dpi: int = 200) -> List[str]:
    """
    Convert DOCX directly to preview images (DOCX -> PDF -> Images)
    
    Args:
        docx_path: Path to the .docx file
        dpi: DPI for image conversion
        
    Returns:
        List of base64-encoded image strings
    """
    try:
        # Convert DOCX to PDF
        pdf_path = docx_to_pdf(docx_path)
        
        # Convert PDF to images
        images = pdf_to_images_base64(pdf_path, dpi=dpi)
        
        # Clean up temporary PDF
        try:
            os.remove(pdf_path)
        except:
            pass
        
        return images
        
    except Exception as e:
        print(f"Error in docx_to_preview_images: {e}")
        raise
