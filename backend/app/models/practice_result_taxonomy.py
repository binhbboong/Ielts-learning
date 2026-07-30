from types import MappingProxyType
from typing import NamedTuple


class QuestionTypeDefinition(NamedTuple):
    key: str
    label: str


READING_QUESTION_TYPES = (
    QuestionTypeDefinition("multiple_choice", "Multiple choice"),
    QuestionTypeDefinition(
        "true_false_not_given",
        "Identifying information (True/False/Not given)",
    ),
    QuestionTypeDefinition(
        "yes_no_not_given",
        "Identifying writer's views/claims (Yes/No/Not given)",
    ),
    QuestionTypeDefinition("matching_information", "Matching information"),
    QuestionTypeDefinition("matching_headings", "Matching headings"),
    QuestionTypeDefinition("matching_features", "Matching features"),
    QuestionTypeDefinition(
        "matching_sentence_endings", "Matching sentence endings"
    ),
    QuestionTypeDefinition("sentence_completion", "Sentence completion"),
    QuestionTypeDefinition(
        "summary_note_table_flow_chart_completion",
        "Summary/note/table/flow-chart completion",
    ),
    QuestionTypeDefinition(
        "diagram_label_completion", "Diagram label completion"
    ),
    QuestionTypeDefinition("short_answer_questions", "Short-answer questions"),
)

LISTENING_QUESTION_TYPES = (
    QuestionTypeDefinition("multiple_choice", "Multiple choice"),
    QuestionTypeDefinition("matching", "Matching"),
    QuestionTypeDefinition(
        "plan_map_diagram_labelling", "Plan/map/diagram labelling"
    ),
    QuestionTypeDefinition(
        "form_note_table_flow_chart_summary_completion",
        "Form/note/table/flow-chart/summary completion",
    ),
    QuestionTypeDefinition("sentence_completion", "Sentence completion"),
    QuestionTypeDefinition("short_answer_questions", "Short-answer questions"),
)

QUESTION_TYPE_TAXONOMY = MappingProxyType(
    {
        "Reading": READING_QUESTION_TYPES,
        "Listening": LISTENING_QUESTION_TYPES,
    }
)
ALLOWED_SKILLS = frozenset(QUESTION_TYPE_TAXONOMY)
