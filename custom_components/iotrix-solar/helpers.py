"""Helper functions for Iotrix Solar integration."""
import re
import base64

def slugify(text: str) -> str:
    """Convert text to a slug (lowercase, no spaces/special chars)."""
    return re.sub(r"[^a-z0-9_]", "", text.lower().replace(" ", "_"))

def base64_to_bytes(base64_str: str) -> bytes:
    """Convert Base64 string to bytes (handle missing padding)."""
    if not base64_str:
        return b""
    # 补充Base64 padding
    padding = len(base64_str) % 4
    if padding != 0:
        base64_str += "=" * (4 - padding)
    return base64.b64decode(base64_str)