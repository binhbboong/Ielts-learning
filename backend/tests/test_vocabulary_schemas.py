import pytest
from pydantic import ValidationError

from app.schemas.vocabulary import VocabularyWordCreate


@pytest.mark.parametrize(
    "field,value",
    [
        ("word", ""),
        ("word", "   "),
        ("meaning", ""),
        ("meaning", "\t"),
    ],
)
def test_word_create_rejects_empty_required_fields(field, value):
    payload = {"word": "ubiquitous", "meaning": "found everywhere"}
    payload[field] = value
    with pytest.raises(ValidationError):
        VocabularyWordCreate(**payload)


def test_word_create_accepts_only_word_and_meaning_and_strips_them():
    payload = VocabularyWordCreate(
        word="  ubiquitous ",
        meaning=" found everywhere ",
    )
    assert payload.word == "ubiquitous"
    assert payload.meaning == "found everywhere"
    assert payload.example is None
    assert payload.topic is None
