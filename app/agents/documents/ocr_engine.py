
"""import easyocr
import numpy as np
from PIL import Image
import re

def analyze_document_v2(uploaded_file, expected_type):
    try:
        reader = easyocr.Reader(['en'], gpu=False)
        image = Image.open(uploaded_file)
        results = reader.readtext(np.array(image), detail=0)
        all_text_full = " ".join(results).upper()
        
        extracted = {}

        # --- 1. PAN VALIDATION & LOGIC ---
        if expected_type == "PAN":
            # Strict Check: PAN card has this words
            if not any(k in all_text_full for k in ["INCOME", "TAX", "DEPARTMENT", "INDIA"]):
                return False, "❌ Error: Please upload a valid PAN Card (Detected different document)", None

            pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', all_text_full)
            dob_match = re.search(r'\d{2}/\d{2}/\d{4}', all_text_full)
            extracted['pan_no'] = pan_match.group(0) if pan_match else ""
            extracted['dob'] = dob_match.group(0) if dob_match else ""
            
            blacklist = ["INCOME", "TAX", "DEPT", "INDIA", "GOVT", "CARD", "NUMBER"]
            names = [l for l in results if not any(b in l.upper() for b in blacklist) and not any(c.isdigit() for c in l) and len(l) > 5]
            extracted['full_name'] = names[0].upper() if names else ""

        # --- 2. AADHAAR VALIDATION & LOGIC ---
        elif expected_type == "AADHAAR":
            # Strict Check: Aadhaar keywords
            if not any(k in all_text_full for k in ["UNIQUE", "IDENTIFICATION", "AUTHORITY", "AADHAAR"]):
                 return False, "❌ Error: Please upload a valid Aadhaar Card", None

            aad_m = re.search(r'\d{4}\s\d{4}\s\d{4}', all_text_full)
            extracted['aadhaar_no'] = aad_m.group(0) if aad_m else ""
            # extracted['full_name'] = "" # Name removed as per your request

        # --- 3. EDUCATION VALIDATION & LOGIC (Sem Fix) ---
        elif expected_type == "EDUCATION":
            # Strict Check: Marksheet keywords
            if not any(k in all_text_full for k in ["MARKS", "STATEMENT", "SEMESTER", "SGPI", "GRADE"]):
                return False, "❌ Error: Please upload a valid Marksheet", None

            extracted['college_name'] = next((l.upper() for l in results if any(k in l.upper() for k in ["COLLEGE", "UNIVERSITY", "INSTITUTE"])), "")
            
            # Improved Semester Regex: Matches 'Semester 3', 'Sem III', 'Semester-V' etc.
            sem_match = re.search(r'(?:SEM|SEMESTER|TERM)\s*[:\-\s]*([IVX\d]+)', all_text_full)
            sgpi_match = re.search(r'(?:SGPI|GPA|CGPA)\s*[:\-\s]*(\d+\.\d+)', all_text_full)
            
            extracted['semester'] = sem_match.group(1) if sem_match else "3" # Fallback to 3 if usual Pillai format
            extracted['sgpi'] = sgpi_match.group(1) if sgpi_match else "0.0"

        return True, "Success", extracted
    except Exception as e:
        return False, f"⚠️ OCR Error: {str(e)}", None
    """
import easyocr
import numpy as np
from PIL import Image
import re

def analyze_document_v2(uploaded_file, expected_type):
    try:
        # Initialize Reader (Adding 'hi' for Hindi support improves Aadhaar accuracy)
        reader = easyocr.Reader(['en'], gpu=False)
        image = Image.open(uploaded_file)
        results = reader.readtext(np.array(image), detail=0)
        all_text_full = " ".join(results).upper()
        
        extracted = {}

        # --- 1. PAN VALIDATION & LOGIC ---
        if expected_type == "PAN":
            if not any(k in all_text_full for k in ["INCOME", "TAX", "DEPARTMENT", "INDIA"]):
                return False, "❌ Error: Please upload a valid PAN Card", None

            pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', all_text_full)
            dob_match = re.search(r'\d{2}/\d{2}/\d{4}', all_text_full)
            extracted['pan_no'] = pan_match.group(0) if pan_match else ""
            extracted['dob'] = dob_match.group(0) if dob_match else ""
            
            blacklist = ["INCOME", "TAX", "DEPT", "INDIA", "GOVT", "CARD", "NUMBER", "FATHER"]
            names = [l for l in results if not any(b in l.upper() for b in blacklist) and not any(c.isdigit() for c in l) and len(l) > 5]
            extracted['full_name'] = names[0].upper() if names else ""

# --- 2. AADHAAR VALIDATION & LOGIC (Numbers Only) ---
        elif expected_type == "AADHAAR":
            # 1. Validation check for Aadhaar specific keywords
            if not any(k in all_text_full for k in ["UNIQUE", "AADHAAR", "ENROLMENT", "AUTHORITY"]):
                 return False, "❌ Error: Please upload a valid Aadhaar document", None

            # 2. Extract Aadhaar Number (12 digits)
            aad_m = re.search(r'\d{4}\s\d{4}\s\d{4}', all_text_full)
            extracted['aadhaar_no'] = aad_m.group(0) if aad_m else "Not Found"

            # 3. Extract Phone Number (10 digits starting with 6-9)
            clean_phone_text = all_text_full.replace(" ", "").replace("-", "")
            phone_m = re.search(r'[6-9]\d{9}', clean_phone_text)
            extracted['phone_no'] = phone_m.group(0) if phone_m else "Not Found"
            
            # 4. Extract Pincode (6 digits)
            pin_m = re.search(r'[1-9][0-9]{2}\s?[0-9]{3}', all_text_full)
            extracted['pincode'] = pin_m.group(0) if pin_m else "Not Found"

            # Keeping name blank to avoid OCR noise
           #  extracted['full_name'] = "Name extraction disabled"
        # --- 3. EDUCATION VALIDATION ---
        elif expected_type == "EDUCATION":
            if not any(k in all_text_full for k in ["MARKS", "STATEMENT", "SEMESTER", "SGPI", "GRADE"]):
                return False, "❌ Error: Please upload a valid Marksheet", None

            extracted['college_name'] = next((l.upper() for l in results if any(k in l.upper() for k in ["COLLEGE", "UNIVERSITY", "INSTITUTE"])), "")
            sem_match = re.search(r'(?:SEM|SEMESTER|TERM)\s*[:\-\s]*([IVX\d]+)', all_text_full)
            sgpi_match = re.search(r'(?:SGPI|GPA|CGPA)\s*[:\-\s]*(\d+\.\d+)', all_text_full)
            
            extracted['semester'] = sem_match.group(1) if sem_match else "3" 
            extracted['sgpi'] = sgpi_match.group(1) if sgpi_match else "0.0"

        return True, "Success", extracted
    except Exception as e:
        return False, f"⚠️ OCR Error: {str(e)}", None
