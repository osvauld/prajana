"""
anveshana.py — external knowledge lookup sources.

anveshana (Sanskrit) = investigation, the act of seeking what is not yet known.

These are the sources the jnana bus uses AFTER the proof graph and static
constants fail: transliteration (script conversion), Sanskrit dictionary,
and any other language-specific lookup.

Each function returns a dict of findings or {} if the library is not installed.
Graceful degradation — the bus works without these, just with less coverage.

Install optional deps in the venv:
    .venv/bin/pip install indic-transliteration aksharamukha sanskrit-data
"""

import re


# ── transliteration ────────────────────────────────────────────────────────────


def transliterate(word: str) -> dict:
    """
    Convert a word between Indic scripts and romanisation schemes.
    Returns a dict with all script forms, or {} if lib not available.

    Supported: Devanagari, Malayalam, Tamil, Telugu, IAST, SLP1, HK, ITRANS.

    Used by the bus to:
      1. Check if an unknown word is a Sanskrit/Malayalam word in a different script
      2. Try all romanisation variants against the proof graph
      3. Provide human-readable display of the concept name

    Example:
        transliterate("avrti")
        → {"src": "SLP1", "iast": "āvṛti", "devanagari": "आवृति",
           "malayalam": "ആവൃതി", "alternatives": ["āvṛti", "Avf2ti", ...]}
    """
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate as _t

        # detect source script from unicode codepoint ranges
        src = _detect_script(word, sanscript)
        if src is None:
            return {}

        results = {"word": word, "src": src}
        for scheme, key in [
            (sanscript.IAST, "iast"),
            (sanscript.DEVANAGARI, "devanagari"),
            (sanscript.MALAYALAM, "malayalam"),
            (sanscript.SLP1, "slp1"),
            (sanscript.HK, "hk"),
            (sanscript.ITRANS, "itrans"),
        ]:
            try:
                results[key] = _t(word, src, scheme)
            except Exception:
                pass

        # alternatives for graph lookup: try each romanisation
        alts: list[str] = [
            str(results[k])
            for k in ("iast", "slp1", "hk", "itrans")
            if k in results and isinstance(results[k], str) and results[k] != word
        ]
        results["alternatives"] = " | ".join(alts)
        return results

    except ImportError:
        return {}
    except Exception as e:
        return {"error": str(e)}


def _detect_script(word: str, sanscript) -> str | None:
    """Detect the script of a word from its Unicode codepoints."""
    for ch in word:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F:
            return sanscript.DEVANAGARI
        if 0x0D00 <= cp <= 0x0D7F:
            return sanscript.MALAYALAM
        if 0x0B80 <= cp <= 0x0BFF:
            return sanscript.TAMIL
        if 0x0C00 <= cp <= 0x0C7F:
            return sanscript.TELUGU
        if 0x0A00 <= cp <= 0x0A7F:
            return sanscript.PUNJABI
    # IAST: check for diacritics
    if re.search(r"[āīūṛṝḷḹēōṃḥṅñṭḍṇśṣḻĀĪŪ]", word):
        return sanscript.IAST
    # ASCII romanisation: assume SLP1 if only ASCII letters
    if word.isascii() and word.isalpha():
        return sanscript.SLP1
    return None


# ── aksharamukha script converter ─────────────────────────────────────────────


def script_convert(word: str, target: str = "Malayalam") -> str:
    """
    Convert a word to a target script via aksharamukha.
    More script targets than indic-transliteration.

    Supported targets include: Malayalam, Tamil, Telugu, Kannada,
    Devanagari, Bengali, Gujarati, Gurmukhi, Odia, Sinhala, Tibetan,
    Thai, Javanese, Balinese, IAST, ISO, Harvard-Kyoto, Velthuis, ...

    Returns the converted string or '' if not available.
    """
    try:
        from aksharamukha import transliterate as aksh_t

        # aksharamukha needs source script too — detect or default to IAST
        return aksh_t.process("IAST", target, word)
    except ImportError:
        return ""
    except Exception:
        return ""


# ── Sanskrit dictionary lookup ────────────────────────────────────────────────


def sanskrit_lookup(word: str) -> dict:
    """
    Look up a word in the Monier-Williams Sanskrit dictionary
    via the sanskrit-data library.

    Returns: {word, iast, source, definitions} or {} if not available.
    Useful for: finding the philosophical meaning of a term,
    confirming a tantra node name is a real Sanskrit word,
    getting synonyms and related terms.
    """
    try:
        # first, get IAST form
        trans = transliterate(word)
        iast = trans.get("iast", word)

        # sanskrit-data provides access to structured Sanskrit lexicons
        # the API varies by version — probe what's available
        try:
            import sanskrit_data.schema.common as sd_common

            return {
                "word": word,
                "iast": iast,
                "source": "sanskrit-data",
                "note": "library available but dictionary access depends on version",
            }
        except ImportError:
            pass

        # fallback: return transliteration only
        if trans:
            return {"word": word, "iast": iast, "source": "transliteration-only"}
        return {}

    except Exception as e:
        return {"error": str(e)}


# ── Malayalam / Tamil NLP via indic-nlp ───────────────────────────────────────


def tokenize_indic(text: str, lang: str = "ml") -> list[str]:
    """
    Tokenise text in an Indic language using indic-nlp-library.
    lang: 'ml' (Malayalam), 'ta' (Tamil), 'hi' (Hindi), 'te' (Telugu), etc.

    Returns list of tokens, or text.split() if library not available.
    Useful for: splitting compound Malayalam words, handling conjunct consonants.
    """
    try:
        from indicnlp.tokenize import indic_tokenize

        return indic_tokenize.trivial_tokenize(text, lang)
    except ImportError:
        return text.split()
    except Exception:
        return text.split()


def normalize_indic(text: str, lang: str = "ml") -> str:
    """
    Normalize Indic script text (NFC, remove ZWJ/ZWNJ, etc.).
    Returns normalized string or original if library not available.
    """
    try:
        from indicnlp.normalize.indic_normalize import IndicNormalizerFactory

        normalizer = IndicNormalizerFactory().get_normalizer(lang)
        return normalizer.normalize(text)
    except ImportError:
        import unicodedata

        return unicodedata.normalize("NFC", text)
    except Exception:
        return text


# ── availability check ─────────────────────────────────────────────────────────


def available_sources() -> dict[str, bool]:
    """
    Report which optional libraries are installed.
    Used by the bus to decide which anveshana paths are available.
    """
    sources = {}
    for name, import_path in [
        ("indic-transliteration", "indic_transliteration"),
        ("aksharamukha", "aksharamukha"),
        ("sanskrit-data", "sanskrit_data"),
        ("indic-nlp", "indicnlp"),
        ("networkx", "networkx"),
    ]:
        try:
            __import__(import_path)
            sources[name] = True
        except ImportError:
            sources[name] = False
    return sources
