def normalize_escapes(value: str) -> str:
    """
    Converts \\n, \\t, \\r, \\uXXXX escape sequences
    into real characters.
    """
    if not isinstance(value, str):
        return value
    try:
        return value.encode().decode("unicode_escape")
    except Exception:
        return value  # fallback safe
