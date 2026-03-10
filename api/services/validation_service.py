import re
from datetime import datetime

GOVERNORATE_CODES = {
    "01": "Cairo",
    "02": "Alexandria",
    "03": "Port Said",
    "04": "Suez",
    "11": "Damietta",
    "12": "Dakahlia",
    "13": "Sharkia",
    "14": "Kalyubia",
    "15": "Kafr El Sheikh",
    "16": "Gharbia",
    "17": "Monufia",
    "18": "Beheira",
    "19": "Ismailia",
    "21": "Giza",
    "22": "Beni Suef",
    "23": "Fayoum",
    "24": "Minya",
    "25": "Assiut",
    "26": "Sohag",
    "27": "Qena",
    "28": "Aswan",
    "29": "Luxor",
    "31": "Red Sea",
    "32": "New Valley",
    "33": "Matrouh",
    "34": "North Sinai",
    "35": "South Sinai",
    "88": "Foreign",
}

def validate_national_id(id_str: str):
    """
    Validates Egyptian National ID and returns a dictionary with extraction results and errors.
    """
    results = {
        "is_valid": True,
        "errors": [],
        "extraction": {
            "century": None,
            "dob": None,
            "governorate": None,
            "gender": None
        }
    }

    if not id_str or not isinstance(id_str, str):
        results["is_valid"] = False
        results["errors"].append("ID must be a string")
        return results

    # Remove spaces and non-digits for initial check
    id_str = re.sub(r"\D", "", id_str)

    if len(id_str) != 14:
        results["is_valid"] = False
        results["errors"].append(f"ID must be 14 digits, found {len(id_str)}")
        return results

    # Century
    century_digit = id_str[0]
    if century_digit == '2':
        century = 1900
    elif century_digit == '3':
        century = 2000
    else:
        results["is_valid"] = False
        results["errors"].append("Invalid century code (first digit must be 2 or 3)")
        century = None
    results["extraction"]["century"] = century

    # Date of Birth
    yy = id_str[1:3]
    mm = id_str[3:5]
    dd = id_str[5:7]

    if century:
        year = century + int(yy)
        try:
            dob = datetime(year, int(mm), int(dd))
            results["extraction"]["dob"] = dob.strftime("%Y-%m-%d")
        except ValueError:
            results["is_valid"] = False
            results["errors"].append(f"Invalid date of birth: {yy}{mm}{dd}")

    # Governorate
    gov_code = id_str[7:9]
    if gov_code in GOVERNORATE_CODES:
        results["extraction"]["governorate"] = GOVERNORATE_CODES[gov_code]
    else:
        results["is_valid"] = False
        results["errors"].append(f"Invalid governorate code: {gov_code}")

    # Sequence Number (digits 10-13)
    # Typically, these are not all zeros.
    sequence_number = id_str[9:13]
    if sequence_number == "0000":
        results["is_valid"] = False
        results["errors"].append("Invalid sequence number (cannot be 0000)")

    # Gender (digit 14)
    gender_digit = int(id_str[13])
    gender = "Male" if gender_digit % 2 != 0 else "Female"
    results["extraction"]["gender"] = gender

    return results

def cross_validate(ocr_data: dict, id_validation: dict):
    """
    Cross-validates OCR extracted fields with National ID validation results.
    """
    cross_errors = []

    # 1. Check if DOB from ID matches Birth-Date from OCR
    id_dob_str = id_validation.get("extraction", {}).get("dob")
    ocr_dob_raw = ocr_data.get("Birth-Date")

    if id_dob_str and ocr_dob_raw:
        # Clean OCR DOB: extract only digits
        ocr_dob_digits = re.sub(r"\D", "", ocr_dob_raw)
        # ID DOB is in YYYY-MM-DD, OCR DOB might be DD/MM/YYYY or similar
        # Extract last 2 digits of year, month, day from ID DOB
        id_date_parts = id_dob_str.split("-") # [YYYY, MM, DD]
        id_yy = id_date_parts[0][2:]
        id_mm = id_date_parts[1]
        id_dd = id_date_parts[2]

        # Check if ID DOB components are present in OCR DOB digits
        # This is a loose check because OCR might return 01-01-1990 as 01011990
        # or just 1/1/1990 as 111990.

        # Strip leading zeros for a looser match
        id_dd_loose = id_dd.lstrip('0') or '0'
        id_mm_loose = id_mm.lstrip('0') or '0'

        if (id_dd not in ocr_dob_digits and id_dd_loose not in ocr_dob_digits) or \
           (id_mm not in ocr_dob_digits and id_mm_loose not in ocr_dob_digits) or \
           id_yy not in ocr_dob_digits:
             # Try a more specific match if ocr_dob_digits has 8 digits (DDMMYYYY)
             match = False
             if len(ocr_dob_digits) == 8:
                 # Assume DDMMYYYY or YYYYMMDD
                 if (ocr_dob_digits[:2] == id_dd and ocr_dob_digits[2:4] == id_mm and ocr_dob_digits[4:] == id_date_parts[0]) or \
                    (ocr_dob_digits[:4] == id_date_parts[0] and ocr_dob_digits[4:6] == id_mm and ocr_dob_digits[6:] == id_dd):
                     match = True

             if not match:
                # Still record as warning/error if they seem different
                # Since OCR can be flaky, we might just add a warning or soft error
                cross_errors.append(f"DOB mismatch: ID says {id_dob_str}, OCR says {ocr_dob_raw}")

    return cross_errors
