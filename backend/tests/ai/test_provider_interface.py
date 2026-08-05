import inspect

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
from app.ai.testing import FakeAIProvider


def _success() -> WritingEvaluationResult:
    criterion = CriterionFeedback(
        band_score=7.0,
        feedback="Specific feedback",
        strengths=["Clear"],
        weaknesses=["Expand"],
    )
    return WritingEvaluationResult(
        status="ok",
        task_response=criterion,
        coherence_and_cohesion=criterion,
        lexical_resource=criterion,
        grammatical_range_and_accuracy=criterion,
        overall_band=7.0,
        corrections=[
            SentenceCorrection(
                original="It improve.",
                corrected="It improves.",
                explanation="Agreement.",
            )
        ],
    )


def test_ai_provider_exposes_six_synchronous_abstract_methods():
    assert inspect.isabstract(AIProvider)
    for method_name in (
        "evaluate_writing",
        "evaluate_speaking",
        "generate_quiz",
        "chat",
        "generate_reading_exercise",
        "generate_listening_script",
    ):
        method = getattr(AIProvider, method_name)
        assert getattr(method, "__isabstractmethod__", False)
        assert not inspect.iscoroutinefunction(method)


def test_fake_provider_can_return_configured_success_and_error():
    success = _success()
    error = WritingEvaluationResult(
        status="error", error_message="provider timeout"
    )
    request = WritingEvaluationRequest(
        response_text="Essay",
        task_type="task2",
        question_text="Question",
    )

    successful_fake = FakeAIProvider(writing_result=success)
    failing_fake = FakeAIProvider(writing_result=error)

    assert isinstance(successful_fake, AIProvider)
    assert successful_fake.evaluate_writing(request) == success
    assert successful_fake.writing_requests == [request]
    assert failing_fake.evaluate_writing(request) == error


def test_fake_provider_implements_the_other_typed_contracts():
    fake = FakeAIProvider(
        speaking_result=SpeakingEvaluationResult(
            status="error", error_message="not configured"
        ),
        quiz_result=QuizGenerationResult(status="ok", questions=["Q"]),
        chat_result=ChatResult(status="ok", message="Answer"),
    )

    assert fake.evaluate_speaking(
        SpeakingEvaluationRequest(
            transcript="Transcript", question_text="Question"
        )
    ).status == "error"
    assert fake.generate_quiz(
        QuizGenerationRequest(topic="Vocabulary", question_count=1)
    ).questions == ["Q"]
    assert fake.chat(ChatRequest(message="Help")).message == "Answer"


def test_fake_provider_implements_generate_reading_exercise():
    question = GeneratedQuestion(
        question_text="What is the passage about?",
        options=["A", "B", "C", "D"],
        correct_option_index=1,
    )
    result = ReadingExerciseGenerationResult(
        status="ok",
        passages=[GeneratedPassage(passage_text="A passage.", questions=[question])],
    )
    fake = FakeAIProvider(reading_exercise_result=result)
    request = ReadingExerciseGenerationRequest(focus_description="the word 'nevertheless'")

    assert fake.generate_reading_exercise(request) == result
    assert fake.reading_exercise_requests == [request]


def test_fake_provider_implements_generate_listening_script():
    question = GeneratedQuestion(
        question_text="What is the script about?",
        options=["A", "B", "C", "D"],
        correct_option_index=1,
    )
    result = ListeningScriptGenerationResult(
        status="ok",
        sections=[GeneratedSection(script_text="A script.", questions=[question])],
    )
    fake = FakeAIProvider(listening_script_result=result)
    request = ListeningScriptGenerationRequest(focus_description="the word 'nevertheless'")

    assert fake.generate_listening_script(request) == result
    assert fake.listening_script_requests == [request]
