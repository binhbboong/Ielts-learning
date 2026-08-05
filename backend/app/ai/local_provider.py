from app.ai.provider import AIProvider
from app.ai.schemas import (
    ChatRequest,
    ChatResult,
    CriterionFeedback,
    GeneratedPassage,
    GeneratedQuestion,
    GeneratedSection,
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


def _beginner_reading_passage(focus: str) -> GeneratedPassage:
    return GeneratedPassage(
        passage_text=(
            f"Local demo passage targeting {focus}. Connect Claude for a real "
            "IELTS-style Reading passage."
        ),
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


def _standard_reading_second_passage(focus: str) -> GeneratedPassage:
    return GeneratedPassage(
        title=f"Local demo passage 2: {focus}",
        passage_text=(
            f"Local demo second passage targeting {focus}, with paragraphs A and B. "
            "Connect Claude for a real IELTS-style Reading passage."
        ),
        questions=[
            GeneratedQuestion(
                question_text="Paragraph A",
                question_type="matching_headings",
                options=["Local demo heading 1", "Local demo heading 2"],
                correct_option_index=0,
                group_instructions=(
                    "Questions: choose the correct heading for each paragraph from "
                    "the list below."
                ),
            ),
            GeneratedQuestion(
                question_text="The passage's summary mentions ___.",
                question_type="summary_completion",
                accepted_answers=["a detail", "detail"],
                group_instructions="Complete the summary below using no more than two words.",
            ),
        ],
    )


def _beginner_listening_section(focus: str) -> GeneratedSection:
    return GeneratedSection(
        context_type="monologue",
        script_text=(
            f"Local demo script targeting {focus}. Connect Claude for a real "
            "IELTS-style Listening script."
        ),
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


def _standard_listening_second_section(focus: str) -> GeneratedSection:
    return GeneratedSection(
        context_type="social_conversation",
        script_text=(
            f"Local demo second script targeting {focus}. Connect Claude for a real "
            "IELTS-style Listening script."
        ),
        questions=[
            GeneratedQuestion(
                question_text="Local demo speaker",
                question_type="matching",
                options=["Local demo option 1", "Local demo option 2"],
                correct_option_index=0,
                group_instructions="Match each speaker to the correct option below.",
            ),
            GeneratedQuestion(
                question_text="Local demo table row ___.",
                question_type="table_completion",
                accepted_answers=["a detail", "detail"],
                group_instructions="Complete the table below using no more than two words.",
            ),
        ],
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
        # Beginner tier: 1 passage (multiple_choice + true_false_not_given).
        # Standard tier adds a 2nd passage (matching_headings +
        # summary_completion) per
        # docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md.
        passages = [_beginner_reading_passage(focus)]
        if request.tier == "standard":
            passages.append(_standard_reading_second_passage(focus))
        return ReadingExerciseGenerationResult(status="ok", passages=passages)

    def generate_listening_script(
        self, request: ListeningScriptGenerationRequest
    ) -> ListeningScriptGenerationResult:
        focus = request.focus_description
        # Beginner tier: 1 section (multiple_choice + note_completion). Standard
        # tier adds a 2nd section (matching + table_completion) per
        # docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md.
        sections = [_beginner_listening_section(focus)]
        if request.tier == "standard":
            sections.append(_standard_listening_second_section(focus))
        return ListeningScriptGenerationResult(status="ok", sections=sections)
