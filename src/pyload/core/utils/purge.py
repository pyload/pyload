import re


def chars(text, chars, repl=""):
    """
    Remove or replace specified characters from a text string.

    Parameters:
    - text (str): The input text to process.
    - chars (str): Characters to match and replace.
    - repl (str): Replacement string for matched characters. Defaults to "".

    Returns:
    - str: The modified text with matched characters replaced.
    """
    chars = chars.replace("\\", "\\\\")
    return re.sub(rf"[{chars}]", repl, text)


_UNIXBADCHARS = ("\0", "/", "\\")
_MACBADCHARS = _UNIXBADCHARS + (":",)
_WINBADCHARS = _MACBADCHARS + ("<", ">", '"', "|", "?", "*")
_WINBADWORDS = (
    "aux",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "con",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
    "nul",
    "prn",
)


def name(text, sep="_", allow_whitespaces=True):
    """
    Sanitize a filename or directory name by removing invalid filesystem characters.

    Replaces invalid characters across Unix, macOS, and Windows platforms with a
    separator, strips leading/trailing whitespaces, and prefixes reserved Windows
    device names (e.g., 'con', 'prn', 'aux', 'nul', 'com1'-'com9', 'lpt1'-'lpt9').

    Parameters:
    - text (str): The filename or directory name to sanitize.
    - sep (str): Replacement string for invalid characters. Defaults to "_".
    - allow_whitespaces (bool): If True, preserve whitespace characters. If False,
      whitespaces are also replaced with the separator. Defaults to True.

    Returns:
    - str: The sanitized filename or directory name.
    """
    bc = uniquify(_WINBADCHARS + _MACBADCHARS + _UNIXBADCHARS)
    repl = r"".join(bc)
    if not allow_whitespaces:
        repl += " "
    res = chars(text, repl, sep).strip()
    if res.lower() in _WINBADWORDS:
        res = (sep or "_") + res
    return res


def pattern(text, rules):
    """
    Apply a series of regex substitution rules sequentially to a text string.

    Each rule in `rules` can be a 2-tuple (pattern, replacement) or a 3-tuple
    (pattern, replacement, flags).

    Parameters:
    - text (str): The input text to process.
    - rules (iterable): An iterable of substitution rules, each represented as a
      tuple of (pattern, replacement) or (pattern, replacement, flags).

    Returns:
    - str: The resulting text after applying all substitution rules.
    """
    for rule in rules:
        try:
            pattr, repl, flags = rule
        except ValueError:
            pattr, repl = rule
            flags = 0
        text = re.sub(pattr, repl, text, flags)
    return text


def truncate(text, to_length):
    """
    Truncate a text string to a target length by replacing middle characters with '~'.
    Useful for truncating long filenames while preserving the start and end of the name.

    Parameters:
    - text (str): The string to truncate.
    - to_length (int): Desired maximum length of the truncated string.

    Returns:
    - str: The truncated string containing the start and end of the original text
      separated by a tilde ('~').

    Raises:
    - OSError: If `to_length` is less than or equal to half the length of `text`.
    """
    min_length = len(text) // 2
    if to_length <= min_length:
        raise OSError("File name too long")
    offset = to_length // 3
    return f"{text[:offset * 2]}~{text[-(offset - 1 + to_length % 3):]}"


def uniquify(seq):
    """
    Remove duplicate items from a sequence while preserving original insertion order.

    Supports unhashable elements such as nested lists, dictionaries, and sets by
    converting them to hashable representations for deduplication tracking.

    Parameters:
    - seq (sequence): An ordered collection (such as a list or tuple) to deduplicate.

    Returns:
    - sequence: A new sequence of the same type as `seq` with duplicates removed.
    """
    seen = set()

    def make_hashable(item):
        """
        Recursively convert an item into a hashable representation.

        Parameters:
        - item (any): The object to convert.

        Returns:
        - any: Hashable equivalent of the item (e.g., tuples for lists, sets, and dicts).
        """
        if isinstance(item, list):
            return tuple(make_hashable(x) for x in item)
        elif isinstance(item, dict):
            return tuple(sorted((k, make_hashable(v)) for k, v in item.items()))
        elif isinstance(item, set):
            return tuple(sorted(make_hashable(x) for x in item))
        return item

    return type(seq)(x for x in seq if not (make_hashable(x) in seen or seen.add(make_hashable(x))))
