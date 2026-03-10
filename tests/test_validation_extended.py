from api.services.validation_service import validate_national_id, GOVERNORATE_CODES

def test_leap_years():
    # 2000 was a leap year
    res = validate_national_id("30002290112347")
    assert res["is_valid"] is True
    assert res["extraction"]["dob"] == "2000-02-29"

    # 1900 was NOT a leap year
    res = validate_national_id("20002290112347")
    assert res["is_valid"] is False
    assert any("Invalid date of birth" in e for e in res["errors"])

    # 2004 was a leap year
    res = validate_national_id("30402290112347")
    assert res["is_valid"] is True
    assert res["extraction"]["dob"] == "2004-02-29"

    # 2023 was NOT a leap year
    res = validate_national_id("32302290112347")
    assert res["is_valid"] is False

def test_all_governorates():
    for code, name in GOVERNORATE_CODES.items():
        id_str = f"2900101{code}12347"
        res = validate_national_id(id_str)
        assert res["is_valid"] is True, f"Failed for governorate {name} ({code})"
        assert res["extraction"]["governorate"] == name

def test_invalid_century():
    # Century code 1 or 4
    assert validate_national_id("19801010112347")["is_valid"] is False
    assert validate_national_id("49801010112347")["is_valid"] is False

def test_invalid_date_components():
    # Month 13
    assert validate_national_id("29813010112347")["is_valid"] is False
    # Day 32
    assert validate_national_id("29801320112347")["is_valid"] is False
    # April 31
    assert validate_national_id("29804310112347")["is_valid"] is False

def test_non_numeric_input():
    # Should strip spaces and still work
    res = validate_national_id("2 98 01 01 01 1234 7")
    assert res["is_valid"] is True
    assert res["extraction"]["dob"] == "1998-01-01"

    # Should fail if non-digits make it too short/long
    assert validate_national_id("2980101011234A")["is_valid"] is False

if __name__ == "__main__":
    test_leap_years()
    test_all_governorates()
    test_invalid_century()
    test_invalid_date_components()
    test_non_numeric_input()
    print("Extended validation tests passed!")
