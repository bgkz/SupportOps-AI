from openai import OpenAI

from backend.schemas.tickets import ReplyDraft


class LLMService:
    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def generate_response(
        self,
        prompt: str,
        instructions: str = "Du bist ein hilfreicher Assistent.",
    ) -> str:
        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
        )

        return response.output_text

    def generate_reply_draft(self, prompt: str, instructions: str) -> ReplyDraft:
        response = self.client.responses.parse(
            model=self.model,
            instructions=instructions,
            input=prompt,
            text_format=ReplyDraft,
        )
        if response.status != "completed" or response.output_parsed is None:
            raise ValueError(
                "Das Modell hat keinen vollst?ndigen Antwortentwurf geliefert."
            )
        return response.output_parsed
