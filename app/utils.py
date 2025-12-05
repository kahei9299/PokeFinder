def parse_limit_offset(
    limit_str: str | None,
    offset_str: str | None,
    *,
    default_limit: int,
    max_limit: int,
) -> tuple[int, int]:
    """
    Parse and validate limit/offset query parameters.

    - If limit_str is None -> use default_limit.
    - If offset_str is None -> use 0.
    - Both must be parseable as integers.
    - 1 <= limit <= max_limit
    - offset >= 0

    On any invalid value, raises ValueError.
    """
    # Parse with defaults
    try:
        if limit_str is None:
            limit = default_limit
        else:
            limit = int(limit_str)

        if offset_str is None:
            offset = 0
        else:
            offset = int(offset_str)
    except ValueError:
        # Non-integer values
        raise ValueError("limit and offset must be integers")

    # Range checks
    if not (1 <= limit <= max_limit):
        raise ValueError("limit out of allowed range")

    if offset < 0:
        raise ValueError("offset must be non-negative")

    return limit, offset
