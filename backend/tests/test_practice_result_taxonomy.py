from app.models.practice_result_taxonomy import (
    QUESTION_TYPE_TAXONOMY,
    QuestionTypeDefinition,
)


def test_taxonomy_is_fixed_distinct_and_uses_stable_keys():
    assert isinstance(QUESTION_TYPE_TAXONOMY["Reading"], tuple)
    assert isinstance(QUESTION_TYPE_TAXONOMY["Listening"], tuple)
    assert all(
        isinstance(option, QuestionTypeDefinition)
        for options in QUESTION_TYPE_TAXONOMY.values()
        for option in options
    )
    assert QUESTION_TYPE_TAXONOMY["Reading"] != QUESTION_TYPE_TAXONOMY["Listening"]
    assert {
        option.key for option in QUESTION_TYPE_TAXONOMY["Reading"]
    } == {
        "multiple_choice",
        "true_false_not_given",
        "yes_no_not_given",
        "matching_information",
        "matching_headings",
        "matching_features",
        "matching_sentence_endings",
        "sentence_completion",
        "summary_note_table_flow_chart_completion",
        "diagram_label_completion",
        "short_answer_questions",
    }
    assert {
        option.key for option in QUESTION_TYPE_TAXONOMY["Listening"]
    } == {
        "multiple_choice",
        "matching",
        "plan_map_diagram_labelling",
        "form_note_table_flow_chart_summary_completion",
        "sentence_completion",
        "short_answer_questions",
    }
