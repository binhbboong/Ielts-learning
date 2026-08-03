import json
import re

from openai import OpenAI

from app.ai.provider import AIProvider
from app.ai.schemas import (
    ChatRequest,
    ChatResult,
    ListeningScriptGenerationRequest,
    ListeningScriptGenerationResult,
    QuizGenerationRequest,
    QuizGenerationResult,
    ReadingExerciseGenerationRequest,
    ReadingExerciseGenerationResult,
    SpeakingEvaluationRequest,
    SpeakingEvaluationResult,
    WritingEvaluationRequest,
    WritingEvaluationResult,
    level_context_line,
)
from app.core.config import settings


class OpenAIProvider(AIProvider):
    def __init__(self, client=None, model: str | None = None):
        self.client = client or OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model or settings.OPENAI_MODEL

    def _generate_json(self, prompt: str, max_output_tokens: int) -> dict:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            max_output_tokens=max_output_tokens,
        )
        raw = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            response.output_text.strip(),
        )
        return json.loads(raw)

    def evaluate_writing(
        self, request: WritingEvaluationRequest
    ) -> WritingEvaluationResult:
        prompt = f"""Evaluate this IELTS Writing {request.task_type} response.
Question: {request.question_text}
Response: {request.response_text}
{level_context_line(request.target_band, request.phase)}
Return JSON only with keys: task_response, coherence_and_cohesion, lexical_resource,
grammatical_range_and_accuracy, overall_band, corrections. Each criterion must contain
band_score, feedback, strengths, weaknesses and cite exact submitted wording. Corrections must
contain at least one object with original, corrected, explanation."""
        try:
            return WritingEvaluationResult(
                status="ok", **self._generate_json(prompt, 2500)
            )
        except Exception as exc:
            return WritingEvaluationResult(
                status="error",
                error_message=f"Writing evaluation failed: {exc}",
            )

    def evaluate_speaking(
        self, request: SpeakingEvaluationRequest
    ) -> SpeakingEvaluationResult:
        prompt = f"""Evaluate this IELTS Speaking transcript against the question.
Question: {request.question_text}
Transcript: {request.transcript}
{level_context_line(request.target_band, request.phase)}
Return JSON only with keys fluency_and_coherence, lexical_resource, and
grammatical_range_and_accuracy. Each must contain band_score, feedback, strengths, weaknesses
and cite exact transcript wording. Do not estimate pronunciation."""
        try:
            return SpeakingEvaluationResult(
                status="ok", **self._generate_json(prompt, 1800)
            )
        except Exception as exc:
            return SpeakingEvaluationResult(
                status="error",
                error_message=f"Speaking evaluation failed: {exc}",
            )

    def generate_quiz(self, request: QuizGenerationRequest) -> QuizGenerationResult:
        raise NotImplementedError

    def chat(self, request: ChatRequest) -> ChatResult:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=request.message,
                max_output_tokens=800,
            )
            return ChatResult(status="ok", message=response.output_text.strip())
        except Exception as exc:
            return ChatResult(
                status="error",
                error_message=f"Chat generation failed: {exc}",
            )

    def generate_reading_exercise(
        self, request: ReadingExerciseGenerationRequest
    ) -> ReadingExerciseGenerationResult:
        prompt = f"""Generate one IELTS-style Reading passage (300-400 words) and 5-8
multiple-choice comprehension questions targeting: {request.focus_description}

Return JSON only with keys: passage_text (string), questions (array of objects with
question_text, options [exactly 4 strings], correct_option_index [0-based int])."""
        try:
            return ReadingExerciseGenerationResult(
                status="ok", **self._generate_json(prompt, 2500)
            )
        except Exception as exc:
            return ReadingExerciseGenerationResult(
                status="error",
                error_message=f"Reading exercise generation failed: {exc}",
            )

    def generate_listening_script(
        self, request: ListeningScriptGenerationRequest
    ) -> ListeningScriptGenerationResult:
        prompt = f"""Generate one IELTS-style Listening script (a short spoken-style
passage, 150-250 words) and 5-8 multiple-choice comprehension questions targeting:
{request.focus_description}

Return JSON only with keys: script_text (string), questions (array of objects with
question_text, options [exactly 4 strings], correct_option_index [0-based int])."""
        try:
            return ListeningScriptGenerationResult(
                status="ok", **self._generate_json(prompt, 2500)
            )
        except Exception as exc:
            return ListeningScriptGenerationResult(
                status="error",
                error_message=f"Listening script generation failed: {exc}",
            )
