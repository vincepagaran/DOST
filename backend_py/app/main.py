from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.validators.form_a import validate_form_a, extract_text_from_image

app = FastAPI(title="DOST Validator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "service": "DOST Validator API", "endpoints": ["/api/validate/formA"]}

@app.get("/health")
def health():
    return {"status": "up"}

@app.post("/api/validate/formA")
async def validate_form_a_endpoint(file: UploadFile = File(...)):
    ct = (file.content_type or "").lower()
    name = (file.filename or "").lower()

    is_pdf = ct in ("application/pdf", "application/x-pdf") or name.endswith(".pdf")
    is_img = any(name.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".heic"))

    if not (is_pdf or is_img):
        raise HTTPException(status_code=400, detail="Only PDF or image (jpg/png) allowed for Form A.")

    blob = await file.read()
    if not blob:
        raise HTTPException(status_code=400, detail="Empty file.")

    if is_img:
        text = extract_text_from_image(blob)
        if not text or len(text) < 50:
            raise HTTPException(status_code=400, detail="Could not extract readable text from image. Please upload a clearer photo/scan.")
        return validate_form_a(None, ocr_text=text)

    # PDF path
    return validate_form_a(blob)
