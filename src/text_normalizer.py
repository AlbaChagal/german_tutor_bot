import re


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
