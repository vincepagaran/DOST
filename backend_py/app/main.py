from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

import os, io, json, traceback

# --------- validator imports (shared helpers) ----------
from app.validators.form_a import (
    validate_form_a,
    extract_text_from_image,
    VALIDATOR_VERSION,
    rasterize_first_page,   # for crops
    _to_px,                 # for crops
    _preproc,               # for crops
)

# -------------------------------------------------------
app = FastAPI(title="DOST Validator API")

# Permissive CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Always return JSON on unexpected errors
@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "traceback": tb,
            "hint": "This is a real backend error. Check the backend console.",
        },
    )

@app.get("/")
def root():
    return {"ok": True, "service": "DOST Validator API", "health": "/health", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "up", "validator_version": VALIDATOR_VERSION}

# ------------------ Form A validation ------------------

@app.options("/api/validate/formA")
async def formA_preflight():
    return JSONResponse({"ok": True})

@app.post("/api/validate/formA")
async def validate_form_a_endpoint(
    file: UploadFile = File(...),
    debug: bool = Query(False, description="Return extra debug info"),
):
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
        # for images, run OCR first (speed + accuracy)
        ocr_text = extract_text_from_image(blob) or ""
        result = validate_form_a(pdf_bytes=None, ocr_text=ocr_text, image_bytes=blob)
    else:
        # for PDFs, pass pdf_bytes (rasterization happens inside validator)
        result = validate_form_a(pdf_bytes=blob, image_bytes=None)

    if debug:
        result["debug"] = {"version": VALIDATOR_VERSION}
    else:
        # keep raw extracted fields out unless debug=true
        result.pop("fields", None)

    return result

# ------------------ Template crops debug ----------------

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "validators", "formA_template.json")

@app.post("/api/template/crops")
async def export_crops(file: UploadFile = File(...)):
    """
    Return a ZIP of cropped images for all template regions.
    Lets you visually check alignment of fields & checkboxes.
    """
    from zipfile import ZipFile, ZIP_DEFLATED

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")

    filename = (file.filename or "").lower()
    is_pdf = filename.endswith(".pdf")

    # Correctly call rasterize_first_page for pdf vs image
    img = rasterize_first_page(
        pdf_bytes=data if is_pdf else None,
        image_bytes=None if is_pdf else data,
        dpi=300,
    )
    if img is None:
        raise HTTPException(400, "Cannot rasterize image/pdf.")

    if not os.path.exists(TEMPLATE_PATH):
        raise HTTPException(400, "Template formA_template.json not found.")
    try:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            tpl = json.load(f)
    except Exception as e:
        raise HTTPException(400, f"Failed to load template JSON: {e}")

    W, H = img.size

    bio = io.BytesIO()
    with ZipFile(bio, "w", ZIP_DEFLATED) as zf:
        # fields
        for f in tpl.get("fields", []):
            key = f["key"]
            x0, y0, x1, y1 = _to_px(f["region"], W, H)
            crop = img.crop((x0, y0, x1, y1))
            crop = _preproc(crop)
            buf = io.BytesIO()
            crop.save(buf, format="PNG")
            zf.writestr(f"fields/{key}.png", buf.getvalue())

        # checkboxes
        for grp in tpl.get("checkboxes", []):
            group_key = grp["key"]
            for opt in grp.get("options", []):
                value = opt["value"]
                x0, y0, x1, y1 = _to_px(opt["region"], W, H)
                crop = img.crop((x0, y0, x1, y1)).convert("L")
                buf = io.BytesIO()
                crop.save(buf, format="PNG")
                zf.writestr(f"checkboxes/{group_key}_{value}.png", buf.getvalue())

    bio.seek(0)
    return StreamingResponse(
        bio,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=crops.zip"},
    )
