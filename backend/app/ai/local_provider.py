from app.ai.provider import AIProvider
from app.ai.schemas import (
    ChatRequest,
    ChatResult,
    CriterionFeedback,
    GeneratedQuestion,
    ListeningScriptGenerationRequest,
    ListeningScriptGenerationResult,
    QuizGenerationRequest,
    QuizGenerationResult,
    ReadingExerciseGenerationRequest,
    ReadingExerciseGenerationResult,
    SentenceCorrection,
    SpeakingEvaluationRequest,
    SpeakingEvaluationResult,
    WritingEvaluationRequest,
    WritingEvaluationResult,
)


def _feedback(reference: str, focus: str) -> CriterionFeedback:
    return CriterionFeedback(
        band_score=6.5,
        feedback=(
            f'Local demo feedback references "{reference}". '
            f"Connect Claude for a real IELTS assessment of {focus}."
        ),
        strengths=[f'The response includes the idea "{reference}".'],
        weaknesses=[f"Develop {focus} with more precise evidence and control."],
    )


class LocalAIProvider(AIProvider):
    """Deterministic, zero-cost provider that keeps the complete local workflow runnable."""

    def evaluate_writing(
        self, request: WritingEvaluationRequest
    ) -> WritingEvaluationResult:
        reference = request.response_text.split(".")[0][:120].strip()
        return WritingEvaluationResult(
            status="ok",
            task_response=_feedback(reference, "task fulfilment"),
            coherence_and_cohesion=_feedback(reference, "paragraph progression"),
            lexical_resource=_feedback(reference, "word choice"),
            grammatical_range_and_accuracy=_feedback(reference, "grammar"),
            overall_band=6.5,
            corrections=[
                SentenceCorrection(
                    original=reference,
                    corrected=reference,
                    explanation=(
                        "Local demo mode preserves the sentence. Connect Claude for "
                        "a genuine correction."
                    ),
                )
            ],
        )

    def evaluate_speaking(
        self, request: SpeakingEvaluationRequest
    ) -> SpeakingEvaluationResult:
        reference = request.transcript.split(".")[0][:120].strip()
        return SpeakingEvaluationResult(
            status="ok",
            fluency_and_coherence=_feedback(reference, "fluency and linking"),
            lexical_resource=_feedback(reference, "spoken vocabulary"),
            grammatical_range_and_accuracy=_feedback(reference, "spoken grammar"),
        )

    def generate_quiz(self, request: QuizGenerationRequest) -> QuizGenerationResult:
        return QuizGenerationResult(
            status="ok",
            questions=[
                f"Local demo question {index + 1} about {request.topic}"
                for index in range(request.question_count)
            ],
        )

    def chat(self, request: ChatRequest) -> ChatResult:
        return ChatResult(status="ok", message=f"Local demo response: {request.message}")

    def generate_reading_exercise(
        self, request: ReadingExerciseGenerationRequest
    ) -> ReadingExerciseGenerationResult:
        focus = request.focus_description
        return ReadingExerciseGenerationResult(
            status="ok",
            passage_text=(
                f"Local demo passage targeting {focus}. Connect Claude for a real "
                "IELTS-style Reading passage."
            ),
            # Beginner-tier catalog (multiple_choice + true_false_not_given) per
            # docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md.
            questions=[
                GeneratedQuestion(
                    question_text=f"Local demo question about {focus}?",
                    question_type="multiple_choice",
                    options=["Option A", "Option B", "Option C", "Option D"],
                    correct_option_index=0,
                ),
                GeneratedQuestion(
                    question_text=f"The passage's main claim relates to {focus}.",
                    question_type="true_false_not_given",
                    options=["True", "False", "Not Given"],
                    correct_option_index=0,
                ),
            ],
        )

    def generate_listening_script(
        self, request: ListeningScriptGenerationRequest
    ) -> ListeningScriptGenerationResult:
        focus = request.focus_description
        return ListeningScriptGenerationResult(
            status="ok",
            script_text=(
                f"Local demo script targeting {focus}. Connect Claude for a real "
                "IELTS-style Listening script."
            ),
            # Beginner-tier catalog (multiple_choice + note_completion) per
            # docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md.
            questions=[
                GeneratedQuestion(
                    question_text=f"Local demo question about {focus}?",
                    question_type="multiple_choice",
                    options=["Option A", "Option B", "Option C", "Option D"],
                    correct_option_index=0,
                ),
                GeneratedQuestion(
                    question_text=f"Complete the note: the speaker mentions ___ ({focus}).",
                    question_type="note_completion",
                    accepted_answers=["a detail", "detail"],
                ),
            ],
        )
