import re
from typing import Dict, Any


class TextNormalizer(object):
    def __init__(self):
        pass

    @staticmethod
    def norm_basic(s: str) -> str:
        s = s.strip()
        s = re.sub(r"\s+", " ", s)
        return s

    @classmethod
    def norm_de_word(cls, w: str) -> str:
        w = cls.norm_basic(w)
        # normalize separable verb notation like auf|hören -> aufhören
        w = w.replace("|", "")
        return w

    @classmethod
    def norm_de_reflexive_verb(cls, v: str) -> str:
        v = cls.norm_de_word(v)
        # normalize reflexive verb notation like "sich erinnern" -> "erinnern"
        v = re.sub(r"^sich\s+", "", v, flags=re.IGNORECASE)
        return v

    @classmethod
    def norm_article_form(cls, s: str) -> str:
        # "<die>Arbeit" -> "<die>arbeit" (article kept, noun lower for comparison)
        s = cls.norm_basic(s)
        m = re.match(r"^<([^>]+)>(.+)$", s)
        if not m:
            return s.lower()
        art = m.group(1).strip().lower()
        noun = m.group(2).strip().lower()
        return f"<{art}>{noun}"

    @staticmethod
    def normalize_to_bot_schema(entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove internal helper fields (pos) and coerce fields to match what bot.py expects.
        """
        pos = entry.get("pos")
        out = {
            "word": entry["word"],
            "explanation_de": entry["explanation_de"],
            "translation_en": entry["translation_en"],
            "example_sentence": entry["example_sentence"],
            "opposite": entry["opposite"],
            "article": entry["article"],
            "level": entry["level"],
            "plural_form": entry["plural_form"],
            "noun_form": entry["noun_form"],
            "verb_form": entry["verb_form"],
        }

        # Enforce schema rules defensively (in case a model regression happens)
        if pos != "noun":
            out["article"] = None
            out["plural_form"] = None

        if pos == "verb":
            out["verb_form"] = None
            # noun_form must be "<article>Nominalisierung"
            if isinstance(out["noun_form"], str) and not out["noun_form"].startswith("<"):
                # best-effort: wrap unknown article as die
                out["noun_form"] = f"<die>{out['noun_form']}"
        elif pos == "noun":
            out["noun_form"] = None
        else:
            out["noun_form"] = None
            out["verb_form"] = None

        # Ensure example sentence contains the exact lemma substring
        if out["word"] not in out["example_sentence"]:
            # best-effort: append a second sentence that includes it exactly
            out["example_sentence"] = out["example_sentence"].rstrip() + f" Heute will ich {out['word']}."

        return out
