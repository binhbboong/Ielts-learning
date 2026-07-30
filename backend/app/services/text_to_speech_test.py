from app.services.text_to_speech import LocalDemoTextToSpeech


def test_local_demo_text_to_speech_returns_playable_audio():
    provider = LocalDemoTextToSpeech()

    result = provider.synthesize("A script about nevertheless.")

    assert result.status == "ok"
    assert result.audio_bytes
    assert result.content_type
