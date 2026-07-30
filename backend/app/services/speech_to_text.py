from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class TranscriptionResult:
    status: Literal["ok", "error"]
    transcript: str | None = None
    error_message: str | None = None

    def __post_init__(self):
        if self.status == "ok" and not self.transcript:
            raise ValueError("successful transcription requires a transcript")
        if self.status == "error" and not self.error_message:
            raise ValueError("failed transcription requires an error message")


class SpeechToText(Protocol):
    def transcribe(self, audio_storage_ref: str) -> TranscriptionResult: ...


class LocalDemoSpeechToText:
    """Runnable local adapter; replace behind this boundary when a vendor is selected."""

    def transcribe(self, audio_storage_ref: str) -> TranscriptionResult:
        return TranscriptionResult(
            status="ok",
            transcript=(
                "Local demo transcript. Configure a speech-to-text vendor to transcribe "
                "the recorded answer verbatim."
            ),
        )


class FakeSpeechToText:
    def __init__(self, result: TranscriptionResult):
        self.result = result
        self.calls: list[str] = []

    def transcribe(self, audio_storage_ref: str) -> TranscriptionResult:
        self.calls.append(audio_storage_ref)
        return self.result


def get_speech_to_text() -> SpeechToText:
    return LocalDemoSpeechToText()
