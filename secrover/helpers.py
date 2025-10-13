def country_code_to_emoji(country_code: str | None) -> str:
    if not country_code or len(country_code) != 2:
        return "❓"
    # Unicode flag calculation
    return "".join(chr(127397 + ord(c.upper())) for c in country_code)
