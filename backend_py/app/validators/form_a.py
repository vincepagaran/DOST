import io
import re
from typing import Dict, Any
from pdfminer.high_level import extract_text

# Optional OCR fallback (for scanned PDFs or images)
try:
    import fitz  # PyMuPDF
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

# -------------------- IMAGE OCR --------------------

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    OCR for single images (jpg/png/tif/heic). Uses Tesseract.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img, lang="eng")
    except Exception as e:
        print("Image OCR error:", e)
        return ""

# -------------------- HELPERS --------------------

BLANK_PATTERNS = re.compile(
    r"""
    ^\s*(
        n/?a | none | null | na | n\.a\.   # N/A variants
        | [_\-\.\u2013\u2014]{2,}          # underscores, lines, dashes
        | [\u25a1\u2610\u25fb\u25a2\s]+     # empty checkbox/boxes: □ ☐ ▫ ▢
    )\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

STOPWORDS_AFTER_VALUE = re.compile(
    r"(?:religion|date of birth|birthdate|place of birth|sex|mobile phone|email address|"
    r"civil status|permanent address|citizenship|city/municipality|province|zipcode|district|"
    r"name of applicant|personal information)", re.I
)

def normalize_unicode(s: str) -> str:
    s = s.replace("\u2013", "-").replace("\u2014", "-")  # – —
    s = s.replace("\u2018", "'").replace("\u2019", "'")  # ‘ ’
    s = s.replace("\u00a0", " ")                         # nbsp
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def to_lower_spaces(s: str) -> str:
    return normalize_unicode(s).lower()

def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        txt = extract_text(io.BytesIO(pdf_bytes)) or ""
    except Exception:
        txt = ""
    return txt

def ocr_pdf(pdf_bytes: bytes, dpi: int = 220) -> str:
    if not OCR_AVAILABLE:
        return ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        chunks = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            txt = pytesseract.image_to_string(img, lang="eng")
            chunks.append(txt)
        doc.close()
        return "\n\n".join(chunks)
    except Exception:
        return ""

def clean_value(v: str | None) -> str:
    if not v:
        return ""
    v = normalize_unicode(v)
    v = STOPWORDS_AFTER_VALUE.split(v, 1)[0]
    v = re.sub(r"\s{2,}", " ", v).strip(" .,:;_-")
    v = re.sub(r"[_\-\u2013\u2014]{2,}", "", v)
    v = re.sub(r"[\u25a1\u2610\u25fb\u25a2]+", "", v)
    return v.strip()

def is_blank(v: str) -> bool:
    if not v:
        return True
    if BLANK_PATTERNS.match(v):
        return True
    if len(v) < 2:
        return True
    return False

def find_labeled_value(text: str, label_variants, max_len=120) -> str | None:
    alt = "|".join([re.escape(lbl) for lbl in label_variants])
    pattern = rf"(?:{alt})\s*:?\s*(?P<val>[^\n\r]{{1,{max_len}}})"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    return clean_value(m.group("val"))

# -------------------- MAIN VALIDATOR --------------------

def validate_form_a(pdf_bytes: bytes | None = None, ocr_text: str | None = None) -> Dict[str, Any]:
    # Determine input source
    if ocr_text is not None:
        text_lc = to_lower_spaces(ocr_text)
    else:
        raw = extract_pdf_text(pdf_bytes)
        text = normalize_unicode(raw)
        text_lc = to_lower_spaces(text)
        if len(text_lc) < 200:
            ocr_txt = to_lower_spaces(ocr_pdf(pdf_bytes))
            if len(ocr_txt) > len(text_lc):
                text_lc = ocr_txt

    # Fingerprint check (Form A only)
    anchors = [
        r"dost\s*-\s*sei|dost\s*sei|dost-sei|dostsei|dost\s*\(?sei\)?",
        r"(s\s*&\s*t|science\s+and\s+technology)",
        r"undergraduate\s+scholarship(?:s)?",
        r"form\s*a",
        r"personal\s*information",
    ]
    missing = [p for p in anchors if not re.search(p, text_lc, re.I)]
    if missing:
        return {
            "valid": False,
            "reason": "This file is not recognized as DOST Form A (fingerprint mismatch).",
            "details": {"missing_anchors": missing}
        }

    # Field extraction
    fields = {
        "name_of_applicant": find_labeled_value(text_lc, [
            "name of applicant", "applicant name", "name of the applicant"
        ]),
        "date_of_birth": find_labeled_value(text_lc, [
            "date of birth", "birthdate"
        ], 40),
        "mobile": find_labeled_value(text_lc, [
            "mobile phone no", "mobile", "contact number", "contact no"
        ], 40),
        "email": find_labeled_value(text_lc, [
            "email address", "email"
        ], 80),
        "permanent_address": find_labeled_value(text_lc, [
            "permanent address", "home address"
        ], 160),
        "city_municipality": find_labeled_value(text_lc, [
            "city/municipality", "municipality", "city"
        ], 80),
        "province": find_labeled_value(text_lc, ["province"], 80),
        "zipcode": find_labeled_value(text_lc, ["zipcode", "zip code"], 10),
        "citizenship": find_labeled_value(text_lc, ["citizenship"], 40),
    }

    errors: Dict[str, str] = {}
    required = [
        "name_of_applicant",
        "date_of_birth",
        "mobile",
        "email",
        "permanent_address",
        "city_municipality",
        "province",
        "zipcode",
        "citizenship",
    ]

    for k in required:
        v = clean_value(fields.get(k) or "")
        if is_blank(v):
            errors[k] = f"{k.replace('_',' ').title()} is missing."

    # Format checks
    if "email" not in errors and fields.get("email"):
        if not re.match(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", fields["email"], re.I):
            errors["email"] = "Email address looks invalid."
    if "mobile" not in errors and fields.get("mobile"):
        if not re.search(r"\d{7,}", fields["mobile"]):
            errors["mobile"] = "Mobile number looks invalid."
    if "zipcode" not in errors and fields.get("zipcode"):
        if not re.search(r"^\d{4}$", fields["zipcode"]):
            errors["zipcode"] = "Zipcode must be 4 digits."

    if errors:
        return {"valid": False, "reason": "Required fields are missing/invalid.", "details": errors, "fields": fields}

    return {"valid": True, "message": "Form A looks valid. All required fields are present.", "fields": fields}
