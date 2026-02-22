"""Randomizer utility wrapping Python's random module with seed support."""
import random
import re
import string
import logging

from faker import Faker

from api_test_data_generator.utils.seed_manager import get_seed

logger = logging.getLogger(__name__)

_faker_instance: Faker | None = None


def get_faker() -> Faker:
    """Return (or create) a seeded Faker instance."""
    global _faker_instance
    if _faker_instance is None:
        seed = get_seed()
        _faker_instance = Faker()
        if seed is not None:
            Faker.seed(seed)
            logger.debug(f"Faker seeded with {seed}")
    return _faker_instance


def reset_faker() -> None:
    """Reset the cached Faker instance (call after changing seed)."""
    global _faker_instance
    _faker_instance = None


def random_string(min_len: int = 5, max_len: int = 20) -> str:
    length = random.randint(min_len, max_len)
    return "".join(random.choices(string.ascii_letters, k=length))


def random_from_regex(pattern: str) -> str:
    """Generate a string matching a regex pattern using rstr if available,
    otherwise fall back to a limited set of common patterns."""
    try:
        import rstr  # type: ignore
        return rstr.xeger(pattern)
    except ImportError:
        # Fallback: handle simple character classes and quantifiers
        result = _simple_regex_gen(pattern)
        return result


def _simple_regex_gen(pattern: str) -> str:
    """Very basic regex pattern generator for common cases."""
    # Replace [A-Z] style with random char from range
    result = pattern
    char_class = re.compile(r"\[([^\]]+)\](\{(\d+),?(\d+)?\}|\*|\+|\?)?")

    def replace_class(m: re.Match) -> str:
        chars = _expand_char_class(m.group(1))
        quantifier = m.group(2) or ""
        count = _resolve_quantifier(quantifier)
        return "".join(random.choices(chars, k=count))

    result = char_class.sub(replace_class, result)

    # Replace \d
    result = re.sub(r"\\d(\{(\d+),?(\d+)?\})?", lambda m: "".join(
        random.choices(string.digits, k=_resolve_quantifier(m.group(1) or ""))
    ), result)

    # Replace \w
    result = re.sub(r"\\w(\{(\d+),?(\d+)?\})?", lambda m: "".join(
        random.choices(string.ascii_letters + string.digits + "_",
                       k=_resolve_quantifier(m.group(1) or ""))
    ), result)

    # Remove anchors
    result = result.replace("^", "").replace("$", "")
    return result


def _expand_char_class(class_str: str) -> list[str]:
    chars: list[str] = []
    i = 0
    while i < len(class_str):
        if i + 2 < len(class_str) and class_str[i + 1] == "-":
            start, end = ord(class_str[i]), ord(class_str[i + 2])
            chars.extend(chr(c) for c in range(start, end + 1))
            i += 3
        else:
            chars.append(class_str[i])
            i += 1
    return chars


def _resolve_quantifier(quantifier: str) -> int:
    if not quantifier:
        return 1
    q = quantifier.strip("{}")
    if "," in q:
        parts = q.split(",")
        lo = int(parts[0]) if parts[0] else 0
        hi = int(parts[1]) if parts[1] else lo + 10
        return random.randint(lo, hi)
    try:
        return int(q)
    except ValueError:
        pass
    if quantifier == "*":
        return random.randint(0, 10)
    if quantifier == "+":
        return random.randint(1, 10)
    if quantifier == "?":
        return random.randint(0, 1)
    return 1
