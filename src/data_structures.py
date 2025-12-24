from typing import List


class ValidationPrompt:
    def __init__(
            self,
            general_task: str,
            specific_task: str,
            rules: List[str],
            input_data: str,
            input_data_prefix: str
    ):
        self.general_task: str = general_task
        self.specific_task: str = specific_task
        self.rules: List[str] = rules
        self.input_data: str = input_data
        self.input_data_prefix: str = input_data_prefix

    def format_prompt(self) -> str:
        rules_formatted = "\n".join(f"- {rule}" for rule in self.rules)
        prompt = (
            f"Task: {self.general_task}\n"
            f"{self.specific_task}\n"
            "Rules:\n"
            f"{rules_formatted}\n" 
            f"\n"
            f"{self.input_data_prefix}: {self.input_data}\n"
        )
        return prompt
