#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from openai import OpenAI

from logger import Logger
from validator import ValidatorConfig, Validator
from text_normalizer import TextNormalizer


# -----------------------------
# Config
# -----------------------------
@dataclass
class GeneratorConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.
    seed: int = 42
    logging_level: str = "info"
    output_path: str = 'database/new_entries.json'

class DataGenerator:
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.logger: Logger = Logger(self.__class__.__name__, logging_level=self.config.logging_level)
        load_dotenv()  # loads OPENAI_API_KEY from .env
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not found. Put it in your .env file.")
        self.client: OpenAI = OpenAI(api_key=api_key)
        self.text_normalizer = TextNormalizer()
        validator = Validator(ValidatorConfig())

    def write_json(self, data: Any) -> None:
        self.logger.info(f'Writing output JSON with {len(data)} words to: {self.config.output_path}')
        path = Path(self.config.output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def load_words(in_path: Union[Path, str]) -> List[str]:

        if isinstance(in_path, str):
            in_path = Path(in_path)
        if not in_path.exists():
            raise FileNotFoundError(f"Words file not found: {in_path}")

        if in_path.suffix.lower() in {".json"}:
            data = json.loads(in_path.read_text(encoding="utf-8"))
            if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
                raise ValueError("JSON words file must be a list of strings.")
            words = [x.strip() for x in data if x.strip()]
            return words

        # default: text
        lines = in_path.read_text(encoding="utf-8").splitlines()
        words = []
        for line in lines:
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                continue
            words.append(s)
        return words

    @property
    def entry_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "word": {"type": "string"},
                "pos": {"type": "string", "enum": ["noun", "verb", "adj", "adv", "other"]},
                "explanation_de": {"type": "string"},
                "translation_en": {"type": "string"},
                "example_sentence": {"type": "string"},
                "opposite": {"type": ["string", "null"]},
                "article": {"type": ["string", "null"], "enum": ["der", "die", "das", None]},
                "level": {"type": ["string", "null"]},
                "plural_form": {"type": ["string", "null"]},
                "noun_form": {"type": ["string", "null"]},
                "verb_form": {"type": ["string", "null"]},
            },
            "required": [
                "word",
                "pos",
                "explanation_de",
                "translation_en",
                "example_sentence",
                "opposite",
                "article",
                "level",
                "plural_form",
                "noun_form",
                "verb_form",
            ],
            "additionalProperties": False,
        }
    @property
    def level_hints(self) -> List[str]:
        return ["A1.1", "A1.2",
               "A2.1", "A2.2",
               "B1.1", "B1.2",
               "B2.1", "B2.2",
               "C1.1", "C1.2",
               "C2.1", "C2.2"]

    def build_prompt(self, word: str) -> str:
        # This prompt is intentionally different from the validation prompts
        # (which ask for candidates given an entry field). Here we generate an entry.
        return f"""
        You are generating a high-quality German vocabulary entry for a learning bot.
        
        Target lemma (exact string): "{word}"
        
        Return a single JSON object that follows the provided JSON schema.
        
        Content requirements:
        - pos: one of noun/verb/adj/adv/other.
        - explanation_de: short, precise definition in German (no translation inside).
        - translation_en: concise English translation (no leading "to" for verbs).
        - example_sentence: a natural German sentence that includes the exact substring "{word}" at least once.
          Use a sentence where a learner could infer the word from context.
        - opposite: a likely antonym (German), or null if not sensible.
        - article/plural_form rules:
          - If pos is noun: set article to der/die/das and plural_form to the plural.
          - Else: article must be null and plural_form must be null.
        - noun_form/verb_form rules:
          - If pos is verb: noun_form must be the nominalization including article in the format "<die>Nominalisierung"
            (choose the correct article). verb_form must be null.
          - If pos is noun: verb_form must be a natural corresponding verb infinitive (e.g. "Optimierung" -> "optimieren"),
            noun_form must be null.
          - Else: noun_form and verb_form must be null.
        - level: choose the most likely CEFR sublevel from: {", ".join(self.level_hints)} or null if uncertain.
        
        Formatting rules:
        - Output only JSON that conforms to the schema.
        - Do not include markdown.
        """.strip()


    def call_openai_with_backoff(self, word: str) -> Dict[str, Any]:
        format: Dict[str, Any]= {
            "format": {
                "type": "json_schema",
                "name": "vocab_entry",
                "schema": self.entry_schema,
                "strict": True,
            }
        }
        try:
            self.logger.info(f'Calling OpenAI for word="{word}"')
            start_build_prompt: float = time.perf_counter()
            prompt = self.build_prompt(word)
            start_call: float = time.perf_counter()
            resp = self.client.responses.create(
                model=self.config.model,
                input=prompt,
                temperature=self.config.temperature,
                text=format,
            )
            start_postprocess: float = time.perf_counter()
            data = json.loads(resp.output_text)
            end: float = time.perf_counter()
            self.logger.info(f'OpenAI call successful for word="{word}"')
            self.logger.debug(f'Timings: '
                              f'build_prompt={(start_call - start_build_prompt)*1000:.1f}ms, '
                              f'call={(start_postprocess - start_call)*1000:.1f}ms, '
                              f'postprocess={(end - start_postprocess)*1000:.1f}ms'
                              f'total={(end - start_build_prompt)*1000:.1f}ms')
            self.logger.debug(f'OpenAI response: {data}')
            return data

        except Exception as e:
            raise RuntimeError(f"OpenAI call failed for word='{word}' after {cfg.max_retries} retries: {e}") from e

    def __call__(self, words: Union[List[str], str]) -> None:
        if isinstance(words, str):
            words = [words]
        assert len(list(set(words))) == len(words), "Input words contain duplicates."

        entries: List[Dict[str, Any]] = []
        for i, w in enumerate(words, start=1):
            data = self.call_openai_with_backoff(w)
            entries.append(self.text_normalizer.normalize_to_bot_schema(data))
            self.logger.info(f"[{i}/{len(words)}] Generated: {w}")

        self.write_json(entries)
        self.logger.info(f"Saved {len(entries)} entries to: {self.config.output_path}")


if __name__ == "__main__":
    cfg = GeneratorConfig()

    words_main = ['Traumphase', 'Tiefschlaf']
    generator = DataGenerator(cfg)
    generator(words_main)
