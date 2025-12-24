from typing import Any, Optional, Dict, List

from data_structures import ValidationPrompt
from prompt_manager_base import PromptManagerBase


class ValidationPromptManager(PromptManagerBase):
    def __init__(self, logging_level: str = "info"):
        super().__init__(logging_level=logging_level)
        self.schema: Optional[Dict[str, Any]] = {
            "type": "object",
            "properties": {
                "candidates": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["candidates"],
            "additionalProperties": False,
        }
        self.task: Optional[str] = "You are validating a German vocabulary database.\n"

    def get_validation_prompt_for_definition(self, definition_de: str, top_k: int) -> ValidationPrompt:
        specific_task: str = (f"Given a dictionary-style German definition, "
                              f"return the most likely {top_k} lemma entries.")
        rules: List[str] = [
            "Candidates must be single German lemmas (or fixed expressions if needed).",
            "Do not include explanations.",
            "If multiple senses exist, prefer the most common B2-level lemma."
        ]
        input_data_prefix: str = "Definition (German)"

        prompt: ValidationPrompt = ValidationPrompt(
            general_task=self.task,
            specific_task=specific_task,
            rules=rules,
            input_data=definition_de,
            input_data_prefix=input_data_prefix
        )
        self.logger.debug(f'Generated prompt for definition:\n{prompt.format_prompt()}')
        return prompt

    def get_validation_prompt_for_antonyms(self, word_de: str, top_k: int) -> ValidationPrompt:
        specific_task: str = f"Return exactly {top_k} German antonyms for the given lemma (or fixed expression)."
        rules: List[str] = [
            "Antonyms must be plausible in common usage.",
            'If antonym is genuinely unclear, include an empty string "" in that slot.'
        ]
        input_data_prefix: str = "Word"

        prompt: ValidationPrompt = ValidationPrompt(
            general_task=self.task,
            specific_task=specific_task,
            rules=rules,
            input_data=word_de,
            input_data_prefix=input_data_prefix
        )
        self.logger.debug(f'Generated prompt for antonyms:\n{prompt.format_prompt()}')
        return prompt

    def get_validation_prompt_for_translations(self, word_de: str, top_k: int) -> ValidationPrompt:
        specific_task: str = f"Return exactly {top_k} concise English translations for the German entry."
        rules: List[str] = [
            "Each candidate should be a short translation phrase.",
            "Prefer comma-free candidates.",
            "do not include the word 'to' before verbs."
        ]
        input_data_prefix: str = "Word"

        prompt: ValidationPrompt = ValidationPrompt(
            general_task=self.task,
            specific_task=specific_task,
            rules=rules,
            input_data=word_de,
            input_data_prefix=input_data_prefix
        )
        self.logger.debug(f'Generated prompt for translations:\n{prompt.format_prompt()}')
        return prompt

    def get_validation_prompt_for_noun_form(self, example_sentence: str, top_k: int) -> ValidationPrompt:
        specific_task: str = f"Given a German verb lemma, return exactly {top_k} candidates, " \
                             f"which are likely nominalizations INCLUDING article"
        rules: List[str] = [
            "Candidates must be single German lemmas (or fixed expressions if needed).",
            "Do not include explanations.",
            "Format each candidate strictly as <article>Nominalization, e.g. <die>Arbeit.\n"
        ]
        input_data_prefix: str = "Verb"

        prompt: ValidationPrompt = ValidationPrompt(
            general_task=self.task,
            specific_task=specific_task,
            rules=rules,
            input_data=example_sentence,
            input_data_prefix=input_data_prefix
        )
        self.logger.debug(f'Generated prompt for noun form:\n{prompt.format_prompt()}')
        return prompt

    def get_validation_prompt_for_verb_form(self, example_sentence: str, top_k: int) -> ValidationPrompt:
        specific_task: str = f"Given a German noun lemma, return exactly {top_k} candidates, " \
                             f"which are likely verbization INCLUDING article"
        rules: List[str] = [
            "Candidates must be single German lemmas (or fixed expressions if needed).",
            "Do not include explanations.",
            "return just the verbs in their 3rd person plural form e.g Arbeit -> arbeiten.\n"
        ]
        input_data_prefix: str = "Verb"

        prompt: ValidationPrompt = ValidationPrompt(
            general_task=self.task,
            specific_task=specific_task,
            rules=rules,
            input_data=example_sentence,
            input_data_prefix=input_data_prefix
        )
        self.logger.debug(f'Generated prompt for noun form:\n{prompt.format_prompt()}')
        return prompt

