import unicodedata
import urllib.parse


# Confusable character map: non-Latin chars that look identical to Latin in common fonts
CONFUSABLE_CHARS = {
    # Cyrillic → Latin
    "\u0430": "a",  # а → a
    "\u0441": "c",  # с → c
    "\u0435": "e",  # е → e
    "\u043e": "o",  # о → o
    "\u0440": "p",  # р → p
    "\u0445": "x",  # х → x
    "\u0456": "i",  # і → i
    "\u0458": "j",  # ј → j
    "\u0455": "s",  # ѕ → s
    "\u04bb": "h",  # һ → h
    "\u0501": "d",  # ԁ → d
    "\u051b": "q",  # ԛ → q
    "\u04cf": "l",  # ӏ → l
    "\u0443": "y",  # у → y
    "\u0432": "v",  # в → v (less convincing but used)
    "\u043a": "k",  # к → k
    "\u043c": "m",  # м → m (less convincing)
    "\u043d": "n",  # н → n (less convincing)
    "\u0437": "z",  # з → z (less convincing)
    # Greek → Latin
    "\u03bf": "o",  # ο → o
    "\u03b1": "a",  # α → a (less convincing but used in attacks)
    # Fullwidth → ASCII (common in CJK phishing)
    "\uff41": "a",  # ａ
    "\uff42": "b",  # ｂ
    "\uff43": "c",  # ｃ
    "\uff44": "d",  # ｄ
    "\uff45": "e",  # ｅ
    "\uff4f": "o",  # ｏ
    "\uff50": "p",  # ｐ
    "\uff53": "s",  # ｓ
}


# Popular domains that are common targets for homograph attacks
PROTECTED_DOMAINS = frozenset({
    "google", "facebook", "amazon", "apple", "microsoft",
    "twitter", "instagram", "youtube", "linkedin", "github",
    "paypal", "netflix", "spotify", "reddit", "wikipedia",
    "whatsapp", "telegram", "discord", "slack", "zoom",
    "dropbox", "yahoo", "tiktok", "snapchat", "pinterest",
    "ebay", "steam",
})


def _get_script(char):
    """Get the Unicode script of a character from its name."""
    try:
        name = unicodedata.name(char, "")
    except ValueError:
        return "UNKNOWN"

    if name.startswith("CYRILLIC"):
        return "CYRILLIC"
    elif name.startswith("GREEK"):
        return "GREEK"
    elif name.startswith("FULLWIDTH"):
        return "FULLWIDTH"
    elif name.startswith("LATIN") or char.isascii():
        return "LATIN"
    else:
        return "OTHER"


def _extract_hostname(url):
    """Extract the hostname from a URL string."""
    if "://" not in url:
        url = "http://" + url

    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname

    if hostname is None:
        return None

    return hostname


def _normalize_domain(hostname):
    """Normalize a hostname by replacing confusable chars with their Latin equivalents."""
    normalized = []
    for char in hostname:
        normalized.append(CONFUSABLE_CHARS.get(char, char))
    return "".join(normalized)


def _find_confusable_chars(hostname):
    """Find all confusable (non-Latin lookalike) characters in a hostname."""
    confusables = []
    for i, char in enumerate(hostname):
        if char in CONFUSABLE_CHARS:
            confusables.append({
                "char": char,
                "position": i,
                "script": _get_script(char),
                "looks_like": CONFUSABLE_CHARS[char]
            })
    return confusables


def _has_mixed_scripts(hostname):
    """Check if a hostname contains characters from multiple scripts."""
    scripts = set()
    for char in hostname:
        if char in (".", "-"):
            continue
        if char.isdigit():
            continue
        script = _get_script(char)
        scripts.add(script)

    # Mixed scripts means more than one non-LATIN script, or LATIN + non-LATIN
    non_latin = scripts - {"LATIN"}
    return len(scripts) > 1 and len(non_latin) > 0


def detect_homograph(url):
    """
    Check if a URL's domain may be an IDN homograph attack.

    Parameters:

        url (str):
            A string representing a URL.

    Returns:

        None if the domain appears safe, or a dict:
            {
                "domain": "gооgle.com",
                "normalized": "google.com",
                "target": "google.com",
                "confusable_chars": [
                    {"char": "о", "position": 1, "script": "CYRILLIC", "looks_like": "o"},
                    ...
                ]
            }

        If suspicious characters are found but no protected domain is matched,
        "target" will be None.
    """
    if url is None:
        return None

    hostname = _extract_hostname(url)

    if hostname is None:
        return None

    # Pure ASCII domains cannot be homograph attacks
    if hostname.isascii():
        return None

    # Check for mixed scripts (the hallmark of homograph attacks)
    if not _has_mixed_scripts(hostname):
        return None

    confusables = _find_confusable_chars(hostname)

    if not confusables:
        return None

    normalized = _normalize_domain(hostname)

    # Check if normalized domain matches a protected domain
    target = None
    # Strip TLD(s) for matching: "google.com" → "google"
    domain_parts = normalized.split(".")
    for part in domain_parts:
        if part in PROTECTED_DOMAINS:
            target = normalized
            break

    return {
        "domain": hostname,
        "normalized": normalized,
        "target": target,
        "confusable_chars": confusables
    }
