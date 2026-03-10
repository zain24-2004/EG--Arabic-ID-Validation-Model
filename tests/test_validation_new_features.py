from api.services.validation_service import validate_national_id, cross_validate

def test_cross_validation():
    # Valid ID and matching OCR data
    id_val = validate_national_id("29801010112347")
    ocr_data = {"Birth-Date": "1998-01-01"}
    errors = cross_validate(ocr_data, id_val)
    assert len(errors) == 0

    # Mismatching DOB
    ocr_data_wrong = {"Birth-Date": "1999-01-01"}
    errors = cross_validate(ocr_data_wrong, id_val)
    assert len(errors) > 0
    assert "DOB mismatch" in errors[0]

    # Partial match (DDMMYYYY)
    ocr_data_fmt = {"Birth-Date": "01011998"}
    errors = cross_validate(ocr_data_fmt, id_val)
    assert len(errors) == 0

    # Another partial match
    ocr_data_fmt2 = {"Birth-Date": "1/1/1998"}
    errors = cross_validate(ocr_data_fmt2, id_val)
    assert len(errors) == 0

def test_sequence_number():
    # Sequence number 0000 should be invalid
    res = validate_national_id("29801010100007")
    assert res["is_valid"] is False
    assert "Invalid sequence number" in res["errors"][0]

if __name__ == "__main__":
    test_cross_validation()
    test_sequence_number()
    print("New validation features tests passed!")
