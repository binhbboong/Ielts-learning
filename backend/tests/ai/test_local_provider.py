from app.ai.local_provider import LocalAIProvider
from app.ai.schemas import (
    TEXT_BASED_QUESTION_TYPES,
    ListeningScriptGenerationRequest,
    ReadingExerciseGenerationRequest,
)


def _assert_option_or_text_shape(question):
    if question.question_type in TEXT_BASED_QUESTION_TYPES:
        assert question.accepted_answers
    else:
        assert 0 <= question.correct_option_index < len(question.options)


def test_local_provider_generates_a_beginner_reading_exercise_referencing_the_focus():
    provider = LocalAIProvider()
    request = ReadingExerciseGenerationRequest(
        focus_description="the word 'nevertheless'", tier="beginner",
    )

    result = provider.generate_reading_exercise(request)

    assert result.status == "ok"
    assert len(result.passages) == 1
    assert "nevertheless" in result.passages[0].passage_text
    question_types = {q.question_type for q in result.passages[0].questions}
    assert question_types == {"multiple_choice", "true_false_not_given"}
    for question in result.passages[0].questions:
        _assert_option_or_text_shape(question)


def test_local_provider_generates_a_standard_reading_exercise_with_two_passages():
    provider = LocalAIProvider()
    request = ReadingExerciseGenerationRequest(
        focus_description="the word 'nevertheless'", tier="standard",
    )

    result = provider.generate_reading_exercise(request)

    assert result.status == "ok"
    assert len(result.passages) == 2
    second_passage_types = {q.question_type for q in result.passages[1].questions}
    assert second_passage_types == {"matching_headings", "summary_completion"}
    for passage in result.passages:
        for question in passage.questions:
            _assert_option_or_text_shape(question)
            if question.question_type in ("matching_headings", "summary_completion"):
                assert question.group_instructions


def test_local_provider_generates_an_advanced_reading_exercise_with_three_passages():
    provider = LocalAIProvider()
    request = ReadingExerciseGenerationRequest(
        focus_description="the word 'nevertheless'", tier="advanced",
    )

    result = provider.generate_reading_exercise(request)

    assert result.status == "ok"
    assert len(result.passages) == 3
    third_passage_types = {q.question_type for q in result.passages[2].questions}
    assert third_passage_types == {
        "matching_information", "matching_features", "flow_chart_completion",
        "diagram_labelling", "short_answer",
    }
    for passage in result.passages:
        for question in passage.questions:
            _assert_option_or_text_shape(question)


def test_local_provider_generates_a_beginner_listening_script_referencing_the_focus():
    provider = LocalAIProvider()
    request = ListeningScriptGenerationRequest(
        focus_description="the word 'nevertheless'", tier="beginner",
    )

    result = provider.generate_listening_script(request)

    assert result.status == "ok"
    assert len(result.sections) == 1
    assert "nevertheless" in result.sections[0].script_text
    question_types = {q.question_type for q in result.sections[0].questions}
    assert question_types == {"multiple_choice", "note_completion"}
    for question in result.sections[0].questions:
        _assert_option_or_text_shape(question)


def test_local_provider_generates_a_standard_listening_script_with_two_sections():
    provider = LocalAIProvider()
    request = ListeningScriptGenerationRequest(
        focus_description="the word 'nevertheless'", tier="standard",
    )

    result = provider.generate_listening_script(request)

    assert result.status == "ok"
    assert len(result.sections) == 2
    assert result.sections[1].context_type == "social_conversation"
    second_section_types = {q.question_type for q in result.sections[1].questions}
    assert second_section_types == {"matching", "table_completion"}
    for section in result.sections:
        for question in section.questions:
            _assert_option_or_text_shape(question)


def test_local_provider_generates_an_advanced_listening_script_with_four_sections():
    provider = LocalAIProvider()
    request = ListeningScriptGenerationRequest(
        focus_description="the word 'nevertheless'", tier="advanced",
    )

    result = provider.generate_listening_script(request)

    assert result.status == "ok"
    assert len(result.sections) == 4
    assert [s.context_type for s in result.sections] == [
        "monologue", "social_conversation", "educational_discussion", "academic_lecture",
    ]
    fourth_section_types = {q.question_type for q in result.sections[3].questions}
    assert fourth_section_types == {"plan_map_diagram_labelling"}
    for section in result.sections:
        for question in section.questions:
            _assert_option_or_text_shape(question)
