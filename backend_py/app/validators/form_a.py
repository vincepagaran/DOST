# backend_py/app/validators/form_a.py
import io
import re
from typing import Dict, Any, Optional, Tuple, List
from pdfminer.high_level import extract_text

# OCR / rasterization
try:
    import fitz  # PyMuPDF
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

# Lightweight CV for checkbox detection
try:
    import numpy as np
    import cv2  # opencv-python-headless
    CV_AVAILABLE = True
except Exception:
    CV_AVAILABLE = False


# ───────────────────────── OCR helpers ─────────────────────────

def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        return extract_text(io.BytesIO(pdf_bytes)) or ""
    except Exception:
        return ""

def ocr_pdf(pdf_bytes: bytes, dpi: int = 220) -> str:
    if not OCR_AVAILABLE:
        return ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        out = []
        for p in doc:
            pix = p.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            out.append(pytesseract.image_to_string(img, lang="eng"))
        doc.close()
        return "\n\n".join(out)
    except Exception:
        return ""

def extract_text_from_image(image_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(img, lang="eng")

def rasterize_first_page(pdf_bytes: Optional[bytes], image_bytes: Optional[bytes], dpi: int = 220) -> Optional["Image.Image"]:
    try:
        if image_bytes is not None:
            return Image.open(io.BytesIO(image_bytes)).convert("RGB")
        if pdf_bytes is not None and OCR_AVAILABLE:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            return img
    except Exception:
        pass
    return None


# ──────────────────────── text utils ───────────────────────────

BLANK_PATTERNS = re.compile(
    r"""
    ^\s*(
        n/?a | none | null | na | n\.a\.
        | [_\-\.\u2013\u2014]{2,}
        | [\u25a1\u2610\u25fb\u25a2\s]+
    )\s*$
    """, re.I | re.X,
)

STOPWORDS_AFTER_VALUE = re.compile(
    r"(?:religion|date of birth|birthdate|place of birth|sex|mobile phone|email address|"
    r"civil status|permanent address|citizenship|city/municipality|province|zipcode|district|"
    r"name of applicant|personal information|order of birth|number of children|deped|learner reference|"
    r"father|mother|spouse|legal guardian|financial contribution|total annual gross income)", re.I
)

def normalize_unicode(s: str) -> str:
    s = s.replace("\u2013", "-").replace("\u2014", "-")  # – —
    s = s.replace("\u2018", "'").replace("\u2019", "'")  # ‘ ’
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def to_lower_spaces(s: str) -> str:
    return normalize_unicode(s).lower()

def clean_value(v: Optional[str]) -> str:
    if not v:
        return ""
    v = normalize_unicode(v)
    v = STOPWORDS_AFTER_VALUE.split(v, 1)[0]
    v = re.sub(r"\s{2,}", " ", v).strip(" .,:;_-")
    v = re.sub(r"[_\-\u2013\u2014]{2,}", "", v)
    v = re.sub(r"[\u25a1\u2610\u25fb\u25a2]+", "", v)
    return v.strip()

def is_blank(v: str) -> bool:
    return not v or BLANK_PATTERNS.match(v) is not None or len(v.strip()) < 2

def find_labeled_value(text: str, label_variants: List[str], max_len: int = 120) -> Optional[str]:
    alt = "|".join([re.escape(x) for x in label_variants])
    m = re.search(rf"(?:{alt})\s*:?\s*(?P<val>[^\n\r]{{1,{max_len}}})", text, re.I)
    return clean_value(m.group("val")) if m else None

def find_money(text: str, label_variants: List[str]) -> Optional[str]:
    alt = "|".join([re.escape(x) for x in label_variants])
    m = re.search(rf"(?:{alt})[^\n\r]{{0,50}}(?P<val>[^\n\r]{{1,80}})", text, re.I)
    if not m:
        return None
    seg = clean_value(m.group("val"))
    n = re.search(r"(?:₱|\bPHP\b)?\s*([0-9][0-9,\.]*)", seg, re.I)
    return n.group(1) if n else seg


# ─────────────────────── Form A fingerprint ────────────────────

FORM_A_HEADER = re.compile(r"form\s*a\s*[-–]\s*personal\s*information", re.I)
OTHER_FORM_TAG = re.compile(r"\bform\s*[b-j]\b", re.I)
FORM_A_LABELS = [r"name of applicant", r"date of birth", r"email address", r"mobile phone no",
                 r"city/municipality", r"province", r"zipcode", r"deped learner reference number"]
FORM_A_LABELS_RE = [re.compile(p, re.I) for p in FORM_A_LABELS]

def looks_like_form_a(text_lc: str) -> bool:
    if not FORM_A_HEADER.search(text_lc):
        return False
    if OTHER_FORM_TAG.search(text_lc):
        return False
    hits = sum(1 for r in FORM_A_LABELS_RE if r.search(text_lc))
    return hits >= 4


# ───────────────────── checkbox detection ──────────────────────

OPTION_KEYS = {
    "sex": ["male", "female"],
    "strand": ["stem", "non-stem", "non stem", "nonstem"],
    "relatives_support": ["yes", "no"],   # III. Financial Contribution question
}

def detect_checkboxes(img_pil: "Image.Image") -> Dict[str, Optional[str]]:
    """
    Heuristic: find square-ish boxes; if the box region has enough ink, it's 'checked'.
    Then, using Tesseract word boxes, tie a short label to the right of each box,
    and map that label to one of our known options.
    """
    out = {"sex": None, "strand": None, "relatives_support": None}
    if not (CV_AVAILABLE and OCR_AVAILABLE):
        return out

    img = np.array(img_pil)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY_INV, 35, 10)
    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = bw.shape[:2]
    area_min, area_max = (h*w) * 0.00001, (h*w) * 0.002
    boxes = []
    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        a = cw * ch
        if a < area_min or a > area_max:  # size filter
            continue
        r = cw / (ch + 1e-6)
        if 0.65 < r < 1.35:
            boxes.append((x, y, cw, ch))

    try:
        d = pytesseract.image_to_data(img_pil, lang="eng", output_type=pytesseract.Output.DICT)
        words = []
        for i in range(len(d["text"])):
            t = (d["text"][i] or "").strip()
            if not t:
                continue
            words.append({"text": t.lower(), "x": d["left"][i], "y": d["top"][i], "w": d["width"][i], "h": d["height"][i]})
    except Exception:
        words = []

    def nearest_phrase(x, y, cw, ch) -> str:
        cx = x + cw
        cy = y + ch//2
        cand = []
        for wd in words:
            if wd["x"] >= cx and abs((wd["y"] + wd["h"]/2) - cy) < max(ch*1.5, 20):
                cand.append((abs(wd["x"] - cx), wd["text"]))
        cand.sort(key=lambda z: z[0])
        return " ".join([t for _, t in cand[:4]])

    def ink_ratio(x, y, cw, ch) -> float:
        roi = bw[max(y,0):min(y+ch,h), max(x,0):min(x+cw,w)]
        if roi.size == 0:
            return 0.0
        return float(np.count_nonzero(roi)) / float(roi.size)

    # checked labels we detected
    detected = []
    for (x, y, cw, ch) in boxes:
        if ink_ratio(x, y, cw, ch) > 0.08:
            detected.append(nearest_phrase(x, y, cw, ch))

    def map_to_option(group: str, phrase: str) -> Optional[str]:
        for opt in OPTION_KEYS[group]:
            if opt in phrase:
                return "non-stem" if (group == "strand" and "non" in opt) else ("stem" if group == "strand" else opt)
        return None

    # Merge to groups (first hit wins)
    for phrase in detected:
        for group in OPTION_KEYS.keys():
            hit = map_to_option(group, phrase)
            if hit and out[group] is None:
                out[group] = hit

    return out


# ───────────────────── main validation ─────────────────────────

def validate_form_a(pdf_bytes: Optional[bytes] = None,
                    ocr_text: Optional[str] = None,
                    image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    # text source
    if ocr_text is not None:
        raw = ocr_text
    else:
        raw = extract_pdf_text(pdf_bytes) if pdf_bytes else ""
        if len(raw) < 200 and pdf_bytes:
            ocr_txt = ocr_pdf(pdf_bytes)
            if len(ocr_txt) > len(raw):
                raw = ocr_txt

    text = normalize_unicode(raw)
    text_lc = to_lower_spaces(text)

    # strict form
    if not looks_like_form_a(text_lc):
        return {
            "valid": False,
            "reason": "Rejected: file is not FORM A – PERSONAL INFORMATION.",
            "missing_fields": {"personal": [], "family": [], "financial": []},
            "stats": {"total": 0, "complete": 0, "percent": 0}
        }

    # ── PERSONAL (text)
    personal_labels = {
        "name_of_applicant": ["name of applicant", "applicant name", "name of the applicant"],
        "date_of_birth": ["date of birth", "birthdate"],
        "mobile": ["mobile phone no", "mobile", "contact number", "contact no"],
        "email": ["email address", "email"],
        "permanent_address": ["permanent address", "home address"],
        "city_municipality": ["city/municipality", "municipality", "city"],
        "province": ["province"],
        "zipcode": ["zipcode", "zip code"],
        "citizenship": ["citizenship"],
    }

    personal_values: Dict[str, str] = {}
    for k, lbls in personal_labels.items():
        personal_values[k] = find_labeled_value(text_lc, lbls, 160 if k == "permanent_address" else 80) or ""

    # ── FAMILY (names only, as requested)
    family_values = {
        "father_name": find_labeled_value(text_lc, ["father name", "father"], 80) or "",
        "mother_name": find_labeled_value(text_lc, ["mother name", "mother"], 80) or "",
    }

    # ── FINANCIAL (total only + relatives yes/no checkbox)
    financial_values = {
        "total_annual_gross_income": find_money(text_lc, [
            "total annual gross income in 2025",
            "total annual gross income in 2024",
            "total annual gross income in 2023",
            "total annual gross income"
        ]) or ""
    }

    # ── checkbox detection
    checkbox = {}
    try:
        img = rasterize_first_page(pdf_bytes, image_bytes)
        if img is not None:
            checkbox = detect_checkboxes(img)
    except Exception:
        checkbox = {}

    # We track these as required checkboxes in "Personal"
    cb_required = {
        "sex": checkbox.get("sex"),                   # 'male' or 'female' (or None)
        "strand": checkbox.get("strand"),             # 'stem' or 'non-stem' (or None)
    }
    # Optional checkbox in Financial (not counted as required, but we return it)
    financial_values["relatives_support"] = checkbox.get("relatives_support")

    # ── Required set (you can tweak)
    required_personal_keys = [
        "name_of_applicant", "date_of_birth", "mobile", "email",
        "permanent_address", "city_municipality", "province", "zipcode", "citizenship",
    ]
    required_family_keys = ["father_name", "mother_name"]
    required_checkbox_keys = ["sex", "strand"]  # part of "Personal" section
    required_financial_keys = ["total_annual_gross_income"]

    # ── compute missing lists
    missing_personal = []
    for k in required_personal_keys:
        if is_blank(personal_values.get(k, "")):
            if k == "name_of_applicant": missing_personal.append("Name of Applicant")
            elif k == "date_of_birth": missing_personal.append("Date of Birth")
            elif k == "mobile": missing_personal.append("Mobile Phone No.")
            elif k == "email": missing_personal.append("Email Address")
            elif k == "permanent_address": missing_personal.append("Permanent Address")
            elif k == "city_municipality": missing_personal.append("City/Municipality")
            elif k == "province": missing_personal.append("Province")
            elif k == "zipcode": missing_personal.append("Zipcode")
            elif k == "citizenship": missing_personal.append("Citizenship")

    for k in required_checkbox_keys:
        if not cb_required.get(k):
            if k == "sex": missing_personal.append("Sex (Male/Female)")
            elif k == "strand": missing_personal.append("Senior High School Strand (STEM/NON-STEM)")

    missing_family = []
    if is_blank(family_values["father_name"]): missing_family.append("NAME: FATHER:")
    if is_blank(family_values["mother_name"]): missing_family.append("NAME: MOTHER:")

    missing_financial = []
    if is_blank(financial_values["total_annual_gross_income"]):
        missing_financial.append("TOTAL ANNUAL GROSS INCOME IN 2025:")

    # ── progress
    tracked_count = len(required_personal_keys) + len(required_checkbox_keys) + len(required_family_keys) + len(required_financial_keys)
    complete = tracked_count - (len(missing_personal) + len(missing_family) + len(missing_financial))
    percent = int(round((complete / tracked_count) * 100)) if tracked_count else 0

    result = {
        "valid": (complete == tracked_count),
        "missing_fields": {
            "personal": missing_personal,
            "family": missing_family,
            "financial": missing_financial,
        },
        "stats": {
            "total": tracked_count,
            "complete": complete,
            "percent": percent
        },
        # also return raw values if you want to display them later
        "fields": {
            **personal_values,
            **family_values,
            **financial_values,
            **cb_required,
        }
    }
    if result["valid"]:
        result["message"] = "Form A looks valid. All required fields are present."
    else:
        result["reason"] = "Some required fields are missing/unchecked."
    return result
