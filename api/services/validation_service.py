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

    # Check if DOB from ID matches Birth-Date from OCR if both exist
    id_dob = id_validation["extraction"]["dob"]
    ocr_dob = ocr_data.get("Birth-Date") # OCR.space might return various formats

    # Note: OCR.space output for Arabic dates might need significant cleaning
    # For now, we just record if they both exist and we could potentially compare them.
    # A robust comparison would involve parsing Arabic date strings.

    return cross_errors
