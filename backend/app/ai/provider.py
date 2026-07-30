from abc import ABC, abstractmethod

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


class AIProvider(ABC):
    @abstractmethod
    def evaluate_writing(
        self, request: WritingEvaluationRequest
    ) -> WritingEvaluationResult:
        raise NotImplementedError

    @abstractmethod
    def evaluate_speaking(
        self, request: SpeakingEvaluationRequest
    ) -> SpeakingEvaluationResult:
        raise NotImplementedError

    @abstractmethod
    def generate_quiz(
        self, request: QuizGenerationRequest
    ) -> QuizGenerationResult:
        raise NotImplementedError

    @abstractmethod
    def chat(self, request: ChatRequest) -> ChatResult:
        raise NotImplementedError

    @abstractmethod
    def generate_reading_exercise(
        self, request: ReadingExerciseGenerationRequest
    ) -> ReadingExerciseGenerationResult:
        raise NotImplementedError

    @abstractmethod
    def generate_listening_script(
        self, request: ListeningScriptGenerationRequest
    ) -> ListeningScriptGenerationResult:
        raise NotImplementedError
