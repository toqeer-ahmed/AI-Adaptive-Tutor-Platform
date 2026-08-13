import pytest
from backend.services.ingestion_service.security import DocumentSecurityValidator, MalwareScanner

def test_magic_bytes_validation_pdf_success():
    valid_pdf_bytes = b"%PDF-1.4 header text content..."
    fmt = DocumentSecurityValidator.validate_magic_bytes(valid_pdf_bytes, "syllabus.pdf")
    assert fmt == "pdf"

def test_magic_bytes_validation_spoof_failure():
    # File named pdf but containing zip signature
    fake_pdf_bytes = b"PK\x03\x04 fake zip content..."
    with pytest.raises(ValueError) as exc:
        DocumentSecurityValidator.validate_magic_bytes(fake_pdf_bytes, "fake.pdf")
    assert "magic byte mismatch" in str(exc.value).lower()

def test_malware_scanner_eicar_detection():
    eicar_bytes = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    is_clean, msg = MalwareScanner.scan_content(eicar_bytes)
    assert is_clean is False
    assert "malware signature detected" in msg.lower()

def test_file_size_limit_enforcement():
    huge_size = 60 * 1024 * 1024 # 60 MB
    with pytest.raises(ValueError) as exc:
        DocumentSecurityValidator.validate_file_metadata("large.pdf", huge_size, "application/pdf")
    assert "exceeds maximum allowed limit" in str(exc.value).lower()
