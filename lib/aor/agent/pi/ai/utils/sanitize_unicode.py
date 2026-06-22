"""Unicode surrogate sanitization.

Python port of vendor/pi-mono-upstream/packages/ai/src/utils/sanitize-unicode.ts.

Context: JS strings are UTF-16; lone surrogate halves (0xD800-0xDBFF without
matching 0xDC00-0xDFFF, or vice versa) are legal in JS but crash many JSON
encoders on the server side. Python strings are logical code points, so this
problem only appears when we interoperate with externally sourced text that
was generated in a UTF-16 context. The function keeps parity with pi-ai so
unicode-surrogate.test.ts ports cleanly.
"""

from __future__ import annotations


def sanitize_surrogates(text: str) -> str:
    """Strip unpaired UTF-16 surrogate halves from `text`.

    Valid multi-code-point sequences (including emoji that code points beyond
    the BMP) pass through untouched; only *lone* surrogate halves are removed.
    """
    if not text:
        return text
    out: list[str] = []
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        code = ord(ch)
        if 0xD800 <= code <= 0xDBFF:
            if i + 1 < length and 0xDC00 <= ord(text[i + 1]) <= 0xDFFF:
                out.append(ch)
                out.append(text[i + 1])
                i += 2
                continue
            i += 1
            continue
        if 0xDC00 <= code <= 0xDFFF:
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


__all__ = ["sanitize_surrogates"]
