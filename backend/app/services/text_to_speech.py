from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class SynthesisResult:
    status: Literal["ok", "error"]
    audio_bytes: bytes | None = None
    content_type: str | None = None
    error_message: str | None = None

    def __post_init__(self):
        if self.status == "ok" and not self.audio_bytes:
            raise ValueError("successful synthesis requires audio bytes")
        if self.status == "error" and not self.error_message:
            raise ValueError("failed synthesis requires an error message")


class TextToSpeech(Protocol):
    def synthesize(self, script_text: str) -> SynthesisResult: ...


class LocalDemoTextToSpeech:
    """Runnable local adapter; replace behind this boundary when a vendor is selected."""

    def synthesize(self, script_text: str) -> SynthesisResult:
        return SynthesisResult(
            status="ok",
            audio_bytes=b"local-demo-audio-placeholder",
            content_type="audio/mpeg",
        )


class FakeTextToSpeech:
    def __init__(self, result: SynthesisResult):
        self.result = result
        self.calls: list[str] = []

    def synthesize(self, script_text: str) -> SynthesisResult:
        self.calls.append(script_text)
        return self.result


def get_text_to_speech() -> TextToSpeech:
    return LocalDemoTextToSpeech()
