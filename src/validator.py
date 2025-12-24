import json
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI

from validation_prompt_manager import ValidationPromptManager
from logger import Logger
from text_normalizer import TextNormalizer


# -----------------------------
# Config
# -----------------------------
@dataclass
class ValidatorConfig:
    model: str = "gpt-4o-mini"
    top_k: int = 3
    temperature: float = 0.0
    max_retries: int = 3
    base_backoff_s: float = 0.8
    seed: int = 42
    logging_level: str = "debug"


# -----------------------------
# Normalization helpers
# -----------------------------

class Validator(object):
    def __init__(self,
                 config: ValidatorConfig):
        self.config = config
        self.logger = Logger(self.__class__.__name__, logging_level=self.config.logging_level)
        self.rnd = random.Random(self.config.seed)

        self.text_normalizer = TextNormalizer()
        load_dotenv()  # loads OPENAI_API_KEY from .env
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY not found. Put it in your .env file.")

        self.client = OpenAI()

        self.candidate_schema = {
            "type": "object",
            "properties": {
                "candidates": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["candidates"],
            "additionalProperties": False,
        }

        self.validation_prompt_manager = ValidationPromptManager(logging_level=self.config.logging_level)

    # -----------------------------
    # OpenAI call with retries
    # -----------------------------
    def call_responses_with_backoff(
            self,
            input_text: str,
            schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        attempt = 0
        while True:
            try:
                self.logger.debug(f'Calling OpenAI with input:\n{input_text}')
                resp = self.client.responses.create(
                    model=self.config.model,
                    input=input_text,
                    temperature=self.config.temperature,
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": "validator_result",
                            "schema": schema,
                            "strict": True,
                        }
                    },
                )
                out = resp.output_text
                self.logger.debug(f'OpenAI output:\n{out}')
                return json.loads(out)

            except Exception as e:
                attempt += 1
                self.logger.error(
                    f'Error on OpenAI call (attempt {attempt} / {self.config.max_retries}): {e}'
                )
                if attempt > self.config.max_retries:
                    raise RecursionError(f'Max retries exceeded for OpenAI call.')

                # Exponential backoff with jitter (recommended for rate limits)
                sleep_s = self.config.base_backoff_s * (2 ** (attempt - 1))
                sleep_s = sleep_s * (0.7 + 0.6 * random.random())
                time.sleep(sleep_s)


    # -----------------------------
    # Field validators
    # -----------------------------
    def is_in_candidates(self, word: str, candidates: List[str]) -> bool:
        w = self.text_normalizer.norm_de_word(word).lower()
        cset = {self.text_normalizer.norm_de_word(c).lower() for c in candidates}
        return w in cset

    def is_in_candidates_article_form(self, noun_form: str, candidates: List[str]) -> bool:
        w = self.text_normalizer.norm_article_form(noun_form)
        cset = {self.text_normalizer.norm_article_form(c) for c in candidates}
        return w in cset

    def validate_entry(self, config: ValidatorConfig, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        word = entry.get("word")

        # 1) explanation_de -> does word appear among candidates?
        input_text: str = self.validation_prompt_manager.get_validation_prompt_for_definition(
            definition_de=entry["explanation_de"],
            top_k=config.top_k
        ).format_prompt()

        if entry.get("explanation_de"):
            data = self.call_responses_with_backoff(
                input_text=input_text,
                schema=self.candidate_schema
            )
            ok = self.is_in_candidates(word, data["candidates"])
            results.append({"field": "explanation_de", "pass": ok, "candidates": data["candidates"]})

        # 2) translation_en -> does DB translation overlap with candidates?
        # Here we split your stored translation by comma and check any token overlap.
        if entry.get("translation_en"):
            data = self.call_responses_with_backoff(
                input_text=self.validation_prompt_manager.get_validation_prompt_for_translations(
                    word_de=word,
                    top_k=config.top_k
                ).format_prompt(),
                schema=self.candidate_schema,
            )
            stored = [t.strip().lower() for t in entry["translation_en"].split(",")]
            cand = [c.strip().lower() for c in data["candidates"]]
            ok = any(s in cand for s in stored)
            results.append({"field": "translation_en", "pass": ok, "candidates": data["candidates"]})

        # 3) example_sentence -> infer target lemma from sentence
        if entry.get("example_sentence"):
            ok = True
            #TODO: create a validation prompt for this
            if False:
                data = self.call_responses_with_backoff(
                    input_text=self.validation_prompt_manager.get_validation_prompt_for_lemma_from_sentence(
                        example_sentence=entry["example_sentence"],
                        top_k=config.top_k
                    ).format_prompt(),
                    schema=self.candidate_schema,
                )
                ok = self.is_in_candidates(word, data["candidates"])
                results.append({"field": "example_sentence", "pass": ok, "candidates": data["candidates"]})

        # 4) opposite -> verify opposite is plausible (word -> antonyms includes stored opposite)
        if entry.get("opposite"):
            data = self.call_responses_with_backoff(
                input_text=self.validation_prompt_manager.get_validation_prompt_for_antonyms(
                    word_de=word,
                    top_k=config.top_k
                ).format_prompt(),
                schema=self.candidate_schema,
            )
            ok = self.is_in_candidates(entry["opposite"], data["candidates"])
            results.append({"field": "opposite", "pass": ok, "candidates": data["candidates"]})

        # 5) noun_form -> if present, verify verb -> noun candidates
        if entry.get("noun_form"):
            data = self.call_responses_with_backoff(
                input_text=self.validation_prompt_manager.get_validation_prompt_for_noun_form(
                    example_sentence=entry["example_sentence"],
                    top_k=config.top_k
                ).format_prompt(),
                schema=self.candidate_schema,
            )
            ok = self.is_in_candidates_article_form(entry["noun_form"], data["candidates"])
            results.append({"field": "noun_form", "pass": ok, "candidates": data["candidates"]})

        return results


# -----------------------------
# Main
# -----------------------------
def main():

    config = ValidatorConfig()
    validator = Validator(config)

    # change this to your json path
    json_path = "/Users/shaharheyman/PycharmProjects/GermanTutorBot/database/update_to_db.json"
    with open(json_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    report = []
    for entry in db:
        entry_results = validator.validate_entry(config, entry)
        if entry_results:
            report.append({"word": entry.get("word"), "results": entry_results})

    out_path = "validation_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Wrote report: {out_path}")
    # Optional: print summary
    total = sum(len(x["results"]) for x in report)
    failed = sum(1 for x in report for r in x["results"] if not r["pass"])
    print(f"Checks: {total}, failed: {failed}")

if __name__ == "__main__":
    main()
