import base64

def bytes_to_base64url(data: bytes) -> str:
    """Encodes bytes to a Base64URL unpadded string."""
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def base64url_to_bytes(data: str) -> bytes:
    """Decodes a Base64URL string (with or without padding) to bytes."""
    # Add padding back if necessary
    padding = '=' * (4 - (len(data) % 4)) if len(data) % 4 != 0 else ''
    return base64.urlsafe_b64decode(data + padding)

def row_to_dict(row):
    """Converts a SQLite Row object to a dictionary."""
    if row is None:
        return None
    return dict(row)

def rows_to_list(rows):
    """Converts a list of SQLite Row objects to a list of dictionaries."""
    return [dict(r) for r in rows] if rows else []
