import re
from typing import Tuple

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024 # 50 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain"
}

class DocumentSecurityValidator:
    @staticmethod
    def validate_file_metadata(file_name: str, content_length: int, mime_type: str) -> None:
        # 1. Size Limit
        if content_length > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum allowed limit of 50 MB ({content_length} bytes).")

        # 2. Extension Check
        ext = ("." + file_name.split(".")[-1].lower()) if "." in file_name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension '{ext}'. Allowed extensions: {ALLOWED_EXTENSIONS}")

        # 3. Executable File Guard
        forbidden_extensions = {".exe", ".bat", ".cmd", ".sh", ".py", ".js", ".vbs", ".dll", ".so", ".elf"}
        if ext in forbidden_extensions:
            raise ValueError("Forbidden executable file format.")

    @staticmethod
    def validate_magic_bytes(content: bytes, file_name: str) -> str:
        """
        Validates magic byte signatures to prevent extension spoofing.
        Returns detected normalized format: 'pdf', 'docx', or 'txt'.
        """
        if len(content) < 4:
            raise ValueError("File content is too small to determine format.")

        # PDF Magic Bytes: %PDF- (\x25\x50\x44\x46\x2d)
        if content.startswith(b"%PDF-"):
            return "pdf"

        # DOCX (ZIP container) Magic Bytes: PK\x03\x04 (\x50\x4b\x03\x04)
        if content.startswith(b"PK\x03\x04"):
            if not file_name.lower().endswith(".docx"):
                raise ValueError("Magic byte mismatch: File is a ZIP container but extension is not .docx")
            return "docx"

        # TXT UTF-8 check
        try:
            content[:1024].decode("utf-8")
            if file_name.lower().endswith(".txt"):
                return "txt"
        except UnicodeDecodeError:
            pass

        raise ValueError("Magic byte validation failed: File content does not match declared extension.")

class MalwareScanner:
    @staticmethod
    def scan_content(content: bytes) -> Tuple[bool, str]:
        """
        Scans file content for malware.
        Returns (is_clean, scan_result_message).
        """
        # Signature check for EICAR anti-malware test string
        eicar_signature = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        if eicar_signature in content:
            return False, "Malware Signature Detected: EICAR test string match."

        return True, "SCAN_CLEAN"
