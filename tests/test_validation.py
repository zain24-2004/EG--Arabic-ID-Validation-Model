from api.services.validation_service import validate_national_id

def test_validation():
    # Valid 1900s Male from Cairo
    res = validate_national_id("29801010112347")
    assert res["is_valid"] is True
    assert res["extraction"]["century"] == 1900
    assert res["extraction"]["dob"] == "1998-01-01"
    assert res["extraction"]["governorate"] == "Cairo"
    assert res["extraction"]["gender"] == "Male"

    # Valid 2000s Female from Giza
    res = validate_national_id("30505052112348")
    assert res["is_valid"] is True
    assert res["extraction"]["century"] == 2000
    assert res["extraction"]["dob"] == "2005-05-05"
    assert res["extraction"]["governorate"] == "Giza"
    assert res["extraction"]["gender"] == "Female"

    # Invalid length
    res = validate_national_id("2980101011234")
    assert res["is_valid"] is False

    # Invalid DOB
    res = validate_national_id("29813010112347")
    assert res["is_valid"] is False

    # Invalid governorate
    res = validate_national_id("29801019912347")
    assert res["is_valid"] is False

if __name__ == "__main__":
    test_validation()
    print("Validation tests passed!")
