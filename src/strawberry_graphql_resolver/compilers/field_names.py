from __future__ import annotations


def selected_top_level_fields(field_names: list[str]) -> list[str]:
    """Return the unique top-level field names implied by *field_names*.

    ``"location { city website }"`` contributes ``"location"``; plain names are
    kept as-is. Order is preserved and duplicates are removed.
    """
    result: list[str] = []
    seen: set[str] = set()
    for name in field_names:
        top = name.split()[0].split("{")[0].strip()
        if not top or top in seen:
            continue
        seen.add(top)
        result.append(top)
    return result
