import json
import re

from openai import OpenAI

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
    level_context_line,
    writing_evaluation_context_line,
)
from app.core.config import settings


class OpenAIProvider(AIProvider):
    def __init__(self, client=None, model: str | None = None):
        self.client = client or OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model or settings.OPENAI_MODEL

    def _generate_json(self, prompt: str, max_output_tokens: int) -> dict:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            max_output_tokens=max_output_tokens,
        )
        raw = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            response.output_text.strip(),
        )
        return json.loads(raw)

    def evaluate_writing(
        self, request: WritingEvaluationRequest
    ) -> WritingEvaluationResult:
        prompt = f"""Evaluate this Writing response for its assigned learning activity.
Question: {request.question_text}
Response: {request.response_text}
{writing_evaluation_context_line(request.target_band, request.phase, request.exercise_type, request.practice_level)}
Return JSON only with keys: task_response, coherence_and_cohesion, lexical_resource,
grammatical_range_and_accuracy, overall_band, corrections. Each criterion must contain
band_score, feedback, strengths, weaknesses and cite exact submitted wording. Corrections must
contain at least one object with original, corrected, explanation."""
        try:
            return WritingEvaluationResult(
                status="ok", **self._generate_json(prompt, 2500)
            )
        except Exception as exc:
            return WritingEvaluationResult(
                status="error",
                error_message=f"Writing evaluation failed: {exc}",
            )

    def evaluate_speaking(
        self, request: SpeakingEvaluationRequest
    ) -> SpeakingEvaluationResult:
        prompt = f"""Evaluate this IELTS Speaking transcript against the question.
Question: {request.question_text}
Transcript: {request.transcript}
{level_context_line(request.target_band, request.phase)}
Return JSON only with keys fluency_and_coherence, lexical_resource, and
grammatical_range_and_accuracy. Each must contain band_score, feedback, strengths, weaknesses
and cite exact transcript wording. Do not estimate pronunciation."""
        try:
            return SpeakingEvaluationResult(
                status="ok", **self._generate_json(prompt, 1800)
            )
        except Exception as exc:
            return SpeakingEvaluationResult(
                status="error",
                error_message=f"Speaking evaluation failed: {exc}",
            )

    def generate_quiz(self, request: QuizGenerationRequest) -> QuizGenerationResult:
        raise NotImplementedError

    def chat(self, request: ChatRequest) -> ChatResult:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=request.message,
                max_output_tokens=800,
            )
            return ChatResult(status="ok", message=response.output_text.strip())
        except Exception as exc:
            return ChatResult(
                status="error",
                error_message=f"Chat generation failed: {exc}",
            )

    def generate_reading_exercise(
        self, request: ReadingExerciseGenerationRequest
    ) -> ReadingExerciseGenerationResult:
        if request.tier == "advanced":
            prompt = f"""Generate three IELTS-style Reading passages (300-400 words each,
increasing difficulty), totaling about 40 questions, targeting: {request.focus_description}

Passage 1: ~13 questions mixing "multiple_choice" and "true_false_not_given". Include
at least one of each.

Passage 2: give it a short "title", ~13 questions mixing "matching_headings" and
"summary_completion". Group each type's questions under a shared group_instructions
string explaining the task.

Passage 3: give it a short "title", ~14 questions mixing "matching_information"
(match a statement to the paragraph it's found in), "matching_features" (match a
feature to what it describes), one of "table_completion"/"flow_chart_completion"
(fill blanks in a table/flow-chart summarizing the passage), "diagram_labelling"
(describe a simple lettered diagram directly in the passage text, e.g. stages
labelled A/B/C, then ask which letter matches a description), and "short_answer"
(a brief factual answer, no more than three words). Group each type's questions
under a shared group_instructions string.

Return JSON only with key: passages (array of 3 objects, each with title [string
or null], passage_text [string], questions [array of objects with question_text,
question_type, group_instructions [string or null], options [array of strings,
required for option-based types — for diagram_labelling, the diagram's labelled
letters], correct_option_index [0-based int indexing into options, required for
option-based types], accepted_answers [array of 1-3 acceptable answer strings,
required for text-based types]])."""
        elif request.tier == "standard":
            prompt = f"""Generate two IELTS-style Reading passages (300-400 words each,
increasing difficulty) targeting: {request.focus_description}

Passage 1: 5-8 questions mixing "multiple_choice" and "true_false_not_given" (a
statement the learner judges against the passage). Include at least one of each.

Passage 2: give it a short "title", and 3-5 questions mixing "matching_headings"
(match a paragraph to the correct heading from a shared list) and
"summary_completion" (fill a blank in a short summary of the passage). Group
each type's questions under a shared group_instructions string explaining the
task (e.g. "Choose the correct heading for each paragraph from the list
below." / "Complete the summary below using no more than two words.").

Return JSON only with key: passages (array of 2 objects, each with title
[string, null for passage 1], passage_text [string], questions [array of
objects with question_text, question_type, group_instructions [string or
null], options [array of strings, required for multiple_choice/
true_false_not_given/matching_headings — exactly 4 for multiple_choice,
exactly ["True", "False", "Not Given"] for true_false_not_given, the shared
heading list for matching_headings], correct_option_index [0-based int
indexing into options, required for option-based types], accepted_answers
[array of 1-3 acceptable answer strings, required for summary_completion]])."""
        else:
            prompt = f"""Generate one IELTS-style Reading passage (300-400 words) and 5-8
comprehension questions targeting: {request.focus_description}

Use a mix of two question types: "multiple_choice" and "true_false_not_given" (a
statement the learner judges against the passage). Include at least one of each.

Return JSON only with key: passages (array of 1 object with title [null],
passage_text [string], questions [array of objects with question_text,
question_type ["multiple_choice" or "true_false_not_given"], options [exactly 4
strings for multiple_choice, exactly ["True", "False", "Not Given"] for
true_false_not_given], correct_option_index [0-based int indexing into
options]])."""
        try:
            max_tokens = 6500 if request.tier == "advanced" else 2500
            return ReadingExerciseGenerationResult(
                status="ok", **self._generate_json(prompt, max_tokens)
            )
        except Exception as exc:
            return ReadingExerciseGenerationResult(
                status="error",
                error_message=f"Reading exercise generation failed: {exc}",
            )

    def generate_listening_script(
        self, request: ListeningScriptGenerationRequest
    ) -> ListeningScriptGenerationResult:
        if request.tier == "advanced":
            prompt = f"""Generate four IELTS-style Listening scripts (short spoken-style
passages, 150-250 words each), totaling about 40 questions, targeting:
{request.focus_description}

Section 1 (context_type "monologue"): ~10 questions mixing "multiple_choice" and
"note_completion". Include at least one of each.

Section 2 (context_type "social_conversation", a short dialogue between two
speakers): ~10 questions mixing "matching" and "table_completion". Group each
type's questions under a shared group_instructions string.

Section 3 (context_type "educational_discussion", a discussion between two
speakers such as a student and a tutor): ~10 questions mixing "form_completion"
and "multiple_choice". Group the form_completion questions under a shared
group_instructions string.

Section 4 (context_type "academic_lecture"): ~10 questions using
"plan_map_diagram_labelling" — describe a simple lettered plan/map/diagram
directly in the script_text (e.g. locations labelled A/B/C), then ask which
letter matches a description. Group them under a shared group_instructions
string.

Return JSON only with key: sections (array of 4 objects, each with
context_type [string], script_text [string], questions [array of objects with
question_text, question_type, group_instructions [string or null], options
[array of strings, required for option-based types — for
plan_map_diagram_labelling, the diagram's labelled letters], correct_option_index
[0-based int indexing into options, required for option-based types],
accepted_answers [array of 1-3 acceptable answer strings, required for
text-based types]])."""
        elif request.tier == "standard":
            prompt = f"""Generate two IELTS-style Listening scripts (short spoken-style
passages, 150-250 words each) targeting: {request.focus_description}

Section 1 (context_type "monologue"): 5-8 questions mixing "multiple_choice" and
"note_completion" (a short fill-in-the-blank note using a word/phrase actually
said in the script). Include at least one of each.

Section 2 (context_type "social_conversation", a short dialogue between two
speakers): 3-5 questions mixing "matching" (match a speaker or item to the
correct option from a shared list) and "table_completion" (fill a blank in a
short table summarizing the conversation). Group each type's questions under a
shared group_instructions string explaining the task.

Return JSON only with key: sections (array of 2 objects, each with
context_type [string], script_text [string], questions [array of objects with
question_text, question_type, group_instructions [string or null], options
[array of strings, required for multiple_choice/matching], correct_option_index
[0-based int indexing into options, required for option-based types],
accepted_answers [array of 1-3 acceptable answer strings, required for
note_completion/table_completion]])."""
        else:
            prompt = f"""Generate one IELTS-style Listening script (a short spoken-style
passage, 150-250 words) and 5-8 comprehension questions targeting:
{request.focus_description}

Use a mix of two question types: "multiple_choice" and "note_completion" (a short
fill-in-the-blank note using a word/phrase actually said in the script). Include at
least one of each.

Return JSON only with key: sections (array of 1 object with context_type
["monologue"], script_text [string], questions [array of objects with
question_text, question_type ["multiple_choice" or "note_completion"], options
[exactly 4 strings, only for multiple_choice questions], correct_option_index
[0-based int indexing into options, only for multiple_choice questions],
accepted_answers [array of 1-3 acceptable answer strings, only for
note_completion questions]])."""
        try:
            max_tokens = 6500 if request.tier == "advanced" else 2500
            return ListeningScriptGenerationResult(
                status="ok", **self._generate_json(prompt, max_tokens)
            )
        except Exception as exc:
            return ListeningScriptGenerationResult(
                status="error",
                error_message=f"Listening script generation failed: {exc}",
            )
