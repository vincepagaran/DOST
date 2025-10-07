# Version tag so /health confirms you’re on this build
VALIDATOR_VERSION = "A5.0-template+hybrid-ocr"

import io, os, re, json
from typing import Dict, Any, Optional, List, Tuple
from pdfminer.high_level import extract_text

# ---- OCR stack (PyMuPDF + Pillow + Tesseract) ----
OCR_AVAILABLE = False
try:
    import fitz  # PyMuPDF
    from PIL import Image, ImageOps, ImageFilter
    import pytesseract

    def _ensure_tesseract() -> bool:
        try:
            cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract")
            if cmd.lower().endswith(".exe") and os.path.exists(cmd):
                _ = pytesseract.get_tesseract_version()
                tdir = os.path.dirname(cmd)
                os.environ.setdefault("TESSDATA_PREFIX", os.path.join(tdir, "tessdata"))
                return True
        except Exception:
            pass
        for c in (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ):
            if os.path.exists(c):
                pytesseract.pytesseract.tesseract_cmd = c
                os.environ.setdefault("TESSDATA_PREFIX", os.path.join(os.path.dirname(c), "tessdata"))
                try:
                    _ = pytesseract.get_tesseract_version()
                    return True
                except Exception:
                    continue
        return False

    if os.name == "nt":
        OCR_AVAILABLE = _ensure_tesseract()
    else:
        try:
            _ = pytesseract.get_tesseract_version()
            OCR_AVAILABLE = True
        except Exception:
            OCR_AVAILABLE = False
except Exception:
    OCR_AVAILABLE = False

# ---- OpenCV (checkbox ink, robust) ----
CV_AVAILABLE = False
try:
    import numpy as np
    import cv2
    CV_AVAILABLE = True
except Exception:
    CV_AVAILABLE = False

# ---- paths / template ----
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "formA_template.json")

# --------------------- helpers ---------------------
def norm(s: str) -> str:
    s = (s or "").replace("\u2013", "-").replace("\u2014", "-").replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def nonempty(v: Optional[str]) -> bool:
    return bool(v and v.strip() and v.strip().lower() not in {"n/a", "na", "none", "null"})

def _preproc(img: "Image.Image") -> "Image.Image":
    g = img.convert("L")
    g = ImageOps.autocontrast(g)
    g = g.filter(ImageFilter.MedianFilter(size=3))
    # slightly higher threshold to suppress lines
    g = g.point(lambda x: 0 if x < 150 else 255, "1")
    return g

def rasterize_first_page(pdf_bytes: Optional[bytes], image_bytes: Optional[bytes], dpi: int = 300) -> Optional["Image.Image"]:
    """
    Return a PIL Image of the first page (at dpi). Works for both:
      - image uploads (jpg/png)
      - PDF uploads (via PyMuPDF)
    IMPORTANT: This must NOT depend on Tesseract; PyMuPDF does not need it.
    """
    try:
        from PIL import Image
        # If an image was sent (jpg/png), just open it
        if image_bytes:
            return Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # If a PDF was sent, rasterize with PyMuPDF regardless of Tesseract
        if pdf_bytes:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if doc.page_count == 0:
                doc.close()
                return None
            page = doc.load_page(0)
            mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            return img
    except Exception:
        return None
    return None


def extract_pdf_text_safe(pdf_bytes: Optional[bytes]) -> str:
    if not pdf_bytes:
        return ""
    try:
        return extract_text(io.BytesIO(pdf_bytes)) or ""
    except Exception:
        return ""

def _load_template() -> Optional[dict]:
    if not os.path.exists(TEMPLATE_PATH):
        return None
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        tpl = json.load(f)
    assert "fields" in tpl and "checkboxes" in tpl
    return tpl

def _to_px(box: List[float], W: int, H: int) -> Tuple[int,int,int,int]:
    x0, y0, x1, y1 = [float(max(0, min(1, v))) for v in box]
    X0, Y0 = int(round(x0*W)), int(round(y0*H))
    X1, Y1 = int(round(x1*W)), int(round(y1*H))
    if X1 <= X0: X1 = X0 + 2
    if Y1 <= Y0: Y1 = Y0 + 2
    return (X0, Y0, X1, Y1)

def _ocr_crop(img: "Image.Image", box: Tuple[int,int,int,int], psm=7, max_len=120) -> str:
    crop = img.crop(box)
    crop = _preproc(crop)
    cfg = f"--psm {psm}"
    txt = pytesseract.image_to_string(crop, lang="eng", config=cfg) if OCR_AVAILABLE else ""
    txt = norm(txt)[:max_len]
    txt = re.sub(r"[_\-]+", "", txt).strip(" .,:;|")
    return txt

def _ink_ratio(gray_roi: "np.ndarray") -> float:
    bw = cv2.adaptiveThreshold(gray_roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 7)
    return float(np.count_nonzero(bw)) / float(bw.size)

def _detect_checkbox(img: "Image.Image", box: Tuple[int,int,int,int], ink_thresh=0.08) -> bool:
    if not CV_AVAILABLE:
        return False
    gray = np.array(_preproc(img).convert("L"))
    x0,y0,x1,y1 = box
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(gray.shape[1], x1); y1 = min(gray.shape[0], y1)
    roi = gray[y0:y1, x0:x1]
    if roi.size == 0: return False
    ink = _ink_ratio(roi)
    if ink > ink_thresh:
        return True
    # OCR micro symbols ✓ X •
    try:
        from PIL import Image as PILImage
        tiny = PILImage.fromarray(roi).convert("L")
        s = pytesseract.image_to_string(tiny, lang="eng", config="--psm 10") if OCR_AVAILABLE else ""
        if re.search(r"[xX✓✔•●■█▣▮▯☑☒]", s or ""):
            return True
    except Exception:
        pass
    return False

def _normalize_money(v: str) -> str:
    v = v.replace("₱", "").replace(",", "").strip()
    m = re.search(r"\d+(?:\.\d{1,2})?", v)
    return m.group(0) if m else ""

# --------------------- MAIN ---------------------
def validate_form_a(pdf_bytes: Optional[bytes] = None,
                    ocr_text: Optional[str] = None,
                    image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Hybrid reader:
      * Rasterize page (300 DPI)
      * Read fields from normalized template boxes (OCR PSM=7)
      * Detect checkboxes by ink
      * Also pull PDF text-layer once and use strict patterns as fallback
    """
    # 0) rasterize + text layer
    img = rasterize_first_page(pdf_bytes, image_bytes, dpi=300)
    if img is None:
        return {"valid": False, "reason": "Cannot rasterize first page.", "missing_fields": {"personal": [], "family": [], "financial": []},
                "filled_fields": {"personal": [], "family": [], "financial": []}, "stats": {"total": 0, "complete": 0, "percent": 0}}
    W, H = img.size
    text_layer = norm(extract_pdf_text_safe(pdf_bytes)).lower() if pdf_bytes else ""

    # 1) load template
    tpl = _load_template()
    if not tpl:
        return {"valid": False, "reason": "Missing formA_template.json.", "missing_fields": {"personal": [], "family": [], "financial": []},
                "filled_fields": {"personal": [], "family": [], "financial": []}, "stats": {"total": 0, "complete": 0, "percent": 0}}

    # 2) read text boxes
    fields: Dict[str, str] = {}
    for f in tpl["fields"]:
        key = f["key"]
        box = _to_px(f["region"], W, H)
        psm = int(f.get("psm", 7))
        mx = int(f.get("max_len", 120))
        val = _ocr_crop(img, box, psm=psm, max_len=mx)
        # strict formats
        if key == "zipcode" and not re.fullmatch(r"\d{4}", val or ""):
            val = ""
        if key == "email" and val:
            v2 = val.replace(" ", "")
            if not re.match(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", v2, re.I):
                val = ""
            else:
                val = v2
        if key in {"father_income", "mother_income", "total_annual_gross_income"}:
            val = _normalize_money(val)
        fields[key] = val

    # 3) read checkboxes
    for grp in tpl["checkboxes"]:
        key = grp["key"]
        chosen = ""
        thr = float(grp.get("ink_thresh", 0.08))
        for opt in grp.get("options", []):
            b = _to_px(opt["region"], W, H)
            if _detect_checkbox(img, b, ink_thresh=thr):
                chosen = opt["value"]
        fields[key] = chosen

    # 4) Fallbacks using text layer (helps filled PDFs)
    if "agusan del norte" in text_layer and not fields.get("province"):
        fields["province"] = "Agusan Del Norte"
    if re.search(r"\b8600\b", text_layer) and not fields.get("zipcode"):
        fields["zipcode"] = "8600"
    if re.search(r"\b09\d{9}\b", text_layer) and not fields.get("mobile"):
        fields["mobile"] = re.search(r"\b09\d{9}\b", text_layer).group(0)
    if re.search(r"\bmale\b", text_layer) and not fields.get("sex"):
        fields["sex"] = "male"
    if re.search(r"\bfemale\b", text_layer) and not fields.get("sex"):
        fields["sex"] = "female"
    if re.search(r"\bstem\b", text_layer) and not fields.get("strand"):
        fields["strand"] = "stem"
    if re.search(r"\bnon[- ]?stem\b", text_layer) and not fields.get("strand"):
        fields["strand"] = "non-stem"

    # ---------- scoring ----------
    personal_rules = [
        ("name_of_applicant","Name of Applicant", nonempty),
        ("date_of_birth","Date of Birth", nonempty),
        ("mobile","Mobile Phone No.", nonempty),
        ("email","Email Address", nonempty),
        ("permanent_address","Permanent Address", nonempty),
        ("city_municipality","City/Municipality", nonempty),
        ("province","Province", nonempty),
        ("zipcode","Zipcode", lambda v: bool(re.fullmatch(r"\d{4}", v or ""))),
        ("citizenship","Citizenship", nonempty),
        ("sex","Sex (Male/Female)", lambda v: v in {"male","female"}),
        ("strand","Senior High School Strand (STEM/NON-STEM)", lambda v: v in {"stem","non-stem"}),
    ]
    filled_personal, missing_personal = [], []
    for k, label, ok in personal_rules:
        (filled_personal if ok(fields.get(k, "")) else missing_personal).append(label)

    family_bases = [
        "name","civil_status","relationship","contact","education",
        "occupation","class_of_worker","employer_name","employer_address","income"
    ]
    filled_family, missing_family = [], []
    for base in family_bases:
        fk, mk = f"father_{base}", f"mother_{base}"
        fl, ml = f"{base.replace('_',' ').upper()}: FATHER:", f"{base.replace('_',' ').upper()}: MOTHER:"
        (filled_family if nonempty(fields.get(fk,"")) else missing_family).append(fl)
        (filled_family if nonempty(fields.get(mk,"")) else missing_family).append(ml)

    fin_rules = [
        ("relatives_support", "Relatives Support (Yes/No)", lambda v: v in {"yes","no"}),
        ("purpose_any", "Purpose of Financial Contribution", nonempty),
        ("relationship_any", "Relationship of Contributor to Applicant", nonempty),
        ("annual_contribution_any", "Annual Contribution (in pesos)", nonempty),
        ("total_annual_gross_income", "TOTAL ANNUAL GROSS INCOME IN 2025:", nonempty),
    ]
    filled_financial, missing_financial = [], []
    for k, label, ok in fin_rules:
        (filled_financial if ok(fields.get(k,"")) else missing_financial).append(label)

    tracked_total = len(personal_rules) + len(family_bases)*2 + len(fin_rules)
    filled_total   = len(filled_personal) + len(filled_family) + len(filled_financial)

    # strict empty guard + noise guard
    any_text_value = any(nonempty(fields.get(k,"")) for k,_,_ in personal_rules if k not in {"sex","strand"})
    any_family_value = any(nonempty(fields.get(f"{who}_{b}","")) for who in ("father","mother") for b in family_bases)
    any_fin_value = any(nonempty(fields.get(k,"")) for k,_,_ in fin_rules)
    any_checkbox = fields.get("sex") in {"male","female"} or fields.get("strand") in {"stem","non-stem"} or fields.get("relatives_support") in {"yes","no"}
    if not any_text_value and not any_family_value and not any_fin_value and not any_checkbox:
        filled_total = 0
    elif filled_total <= tracked_total * 0.2:
        filled_total = 0

    percent = int(round((filled_total / tracked_total) * 100)) if tracked_total else 0

    result = {
        "valid": filled_total == tracked_total,
        "missing_fields": {
            "personal":  missing_personal,
            "family":    missing_family,
            "financial": missing_financial,
        },
        "filled_fields": {
            "personal":  filled_personal,
            "family":    filled_family,
            "financial": filled_financial,
        },
        "stats": {"total": tracked_total, "complete": filled_total, "percent": percent},
        "fields": fields,  # hidden unless debug=1 by your main.py
    }
    if result["valid"]:
        result["message"] = "Form A looks valid. All required fields are present."
    else:
        result["reason"] = "Some required fields are missing/unchecked."
    return result


# kept public for main.py debug endpoint
def extract_text_from_image(image_bytes: bytes) -> str:
    if not OCR_AVAILABLE:
        return ""
    from PIL import Image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = _preproc(img)
    txt = pytesseract.image_to_string(img, lang="eng")
    lines = [l.strip() for l in txt.splitlines() if len(l.strip()) > 2 and not re.fullmatch(r"[_\-]+", l.strip())]
    return "\n".join(lines)
