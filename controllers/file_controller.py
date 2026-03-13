from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
import io

async def extract_text_from_pdf(file: UploadFile):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        content = await file.read()
        pdf_reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF. It might be an image-only PDF.")
            
        return {
            "success": True,
            "filename": file.filename,
            "text": text
        }
    except Exception as e:
        print(f"PDF Extraction Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
