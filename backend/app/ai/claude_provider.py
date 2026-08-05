import json
import re

import anthropic

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


class ClaudeProvider(AIProvider):
    def __init__(self, client=None, model: str = "claude-3-5-haiku-latest"):
        self.client = client or anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = model

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
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
            return WritingEvaluationResult(status="ok", **json.loads(raw))
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
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1800,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
            return SpeakingEvaluationResult(status="ok", **json.loads(raw))
        except Exception as exc:
            return SpeakingEvaluationResult(
                status="error",
                error_message=f"Speaking evaluation failed: {exc}",
            )

    def generate_quiz(self, request: QuizGenerationRequest) -> QuizGenerationResult:
        raise NotImplementedError

    def chat(self, request: ChatRequest) -> ChatResult:
        raise NotImplementedError

    def generate_reading_exercise(
        self, request: ReadingExerciseGenerationRequest
    ) -> ReadingExerciseGenerationResult:
        prompt = f"""Generate one IELTS-style Reading passage (300-400 words) and 5-8
comprehension questions targeting: {request.focus_description}

Use a mix of two question types: "multiple_choice" and "true_false_not_given" (a
statement the learner judges against the passage). Include at least one of each.

Return JSON only with keys: passage_text (string), questions (array of objects with
question_text, question_type ["multiple_choice" or "true_false_not_given"], options
[exactly 4 strings for multiple_choice, exactly ["True", "False", "Not Given"] for
true_false_not_given], correct_option_index [0-based int indexing into options])."""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
            return ReadingExerciseGenerationResult(status="ok", **json.loads(raw))
        except Exception as exc:
            return ReadingExerciseGenerationResult(
                status="error",
                error_message=f"Reading exercise generation failed: {exc}",
            )

    def generate_listening_script(
        self, request: ListeningScriptGenerationRequest
    ) -> ListeningScriptGenerationResult:
        prompt = f"""Generate one IELTS-style Listening script (a short spoken-style
passage, 150-250 words) and 5-8 comprehension questions targeting:
{request.focus_description}

Use a mix of two question types: "multiple_choice" and "note_completion" (a short
fill-in-the-blank note using a word/phrase actually said in the script). Include at
least one of each.

Return JSON only with keys: script_text (string), questions (array of objects with
question_text, question_type ["multiple_choice" or "note_completion"], options
[exactly 4 strings, only for multiple_choice questions], correct_option_index
[0-based int indexing into options, only for multiple_choice questions],
accepted_answers [array of 1-3 acceptable answer strings, only for note_completion
questions])."""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
            return ListeningScriptGenerationResult(status="ok", **json.loads(raw))
        except Exception as exc:
            return ListeningScriptGenerationResult(
                status="error",
                error_message=f"Listening script generation failed: {exc}",
            )
