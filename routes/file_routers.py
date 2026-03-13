from fastapi import APIRouter, UploadFile, File
from controllers.file_controller import extract_text_from_pdf

router = APIRouter(prefix="/file")

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    return await extract_text_from_pdf(file)
