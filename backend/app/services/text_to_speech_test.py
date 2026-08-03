from app.services.text_to_speech import LocalDemoTextToSpeech, OpenAITextToSpeech


def test_local_demo_text_to_speech_returns_playable_audio():
    provider = LocalDemoTextToSpeech()

    result = provider.synthesize("A script about nevertheless.")

    assert result.status == "ok"
    assert result.audio_bytes
    assert result.content_type


class _FakeSpeechResponse:
    content = b"valid-mp3-bytes"


class _FakeSpeech:
    def create(self, **kwargs):
        return _FakeSpeechResponse()


class _FakeAudio:
    speech = _FakeSpeech()


class _FakeOpenAIClient:
    audio = _FakeAudio()


def test_openai_text_to_speech_returns_audio():
    result = OpenAITextToSpeech(client=_FakeOpenAIClient()).synthesize("Hello")

    assert result.status == "ok"
    assert result.audio_bytes == b"valid-mp3-bytes"
    assert result.content_type == "audio/mpeg"
