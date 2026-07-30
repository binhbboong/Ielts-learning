import time

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
)


class FakeAIProvider(AIProvider):
    def __init__(
        self,
        *,
        writing_result: WritingEvaluationResult | None = None,
        speaking_result: SpeakingEvaluationResult | None = None,
        quiz_result: QuizGenerationResult | None = None,
        chat_result: ChatResult | None = None,
        reading_exercise_result: ReadingExerciseGenerationResult | None = None,
        listening_script_result: ListeningScriptGenerationResult | None = None,
        writing_delay_seconds: float = 0,
    ):
        self.writing_result = writing_result or WritingEvaluationResult(
            status="error", error_message="writing result not configured"
        )
        self.speaking_result = speaking_result or SpeakingEvaluationResult(
            status="error", error_message="speaking result not configured"
        )
        self.quiz_result = quiz_result or QuizGenerationResult(
            status="error", error_message="quiz result not configured"
        )
        self.chat_result = chat_result or ChatResult(
            status="error", error_message="chat result not configured"
        )
        self.reading_exercise_result = reading_exercise_result or ReadingExerciseGenerationResult(
            status="error", error_message="reading exercise result not configured"
        )
        self.listening_script_result = listening_script_result or ListeningScriptGenerationResult(
            status="error", error_message="listening script result not configured"
        )
        self.writing_delay_seconds = writing_delay_seconds
        self.writing_requests: list[WritingEvaluationRequest] = []
        self.speaking_requests: list[SpeakingEvaluationRequest] = []
        self.quiz_requests: list[QuizGenerationRequest] = []
        self.chat_requests: list[ChatRequest] = []
        self.reading_exercise_requests: list[ReadingExerciseGenerationRequest] = []
        self.listening_script_requests: list[ListeningScriptGenerationRequest] = []

    def evaluate_writing(
        self, request: WritingEvaluationRequest
    ) -> WritingEvaluationResult:
        self.writing_requests.append(request)
        if self.writing_delay_seconds:
            time.sleep(self.writing_delay_seconds)
        return self.writing_result

    def evaluate_speaking(
        self, request: SpeakingEvaluationRequest
    ) -> SpeakingEvaluationResult:
        self.speaking_requests.append(request)
        return self.speaking_result

    def generate_quiz(
        self, request: QuizGenerationRequest
    ) -> QuizGenerationResult:
        self.quiz_requests.append(request)
        return self.quiz_result

    def chat(self, request: ChatRequest) -> ChatResult:
        self.chat_requests.append(request)
        return self.chat_result

    def generate_reading_exercise(
        self, request: ReadingExerciseGenerationRequest
    ) -> ReadingExerciseGenerationResult:
        self.reading_exercise_requests.append(request)
        return self.reading_exercise_result

    def generate_listening_script(
        self, request: ListeningScriptGenerationRequest
    ) -> ListeningScriptGenerationResult:
        self.listening_script_requests.append(request)
        return self.listening_script_result
