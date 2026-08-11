from dataclasses import dataclass


@dataclass(frozen=True)
class WritingLevelConfig:
    level: int
    exercise_type: str
    label: str
    objective: str
    min_sentences: int
    max_sentences: int
    min_words: int
    max_words: int
    sentence_frames: tuple[str, ...] = ()
    show_ielts_band: bool = False


_PHASE_CONFIGS = {
    "foundation": WritingLevelConfig(
        level=1,
        exercise_type="sentence_building",
        label="Sentence foundations",
        objective="Write a few clear, complete sentences about one familiar idea.",
        min_sentences=1,
        max_sentences=3,
        min_words=8,
        max_words=40,
        sentence_frames=(
            "I usually ...",
            "I like ... because ...",
            "It is ... and ...",
        ),
    ),
    "core_skills": WritingLevelConfig(
        level=2,
        exercise_type="sentence_expansion",
        label="Connect and expand",
        objective="Develop one idea across several connected sentences.",
        min_sentences=4,
        max_sentences=6,
        min_words=40,
        max_words=80,
        sentence_frames=(
            "First, ...",
            "This is because ...",
            "For example, ...",
            "However, ...",
        ),
    ),
    "development": WritingLevelConfig(
        level=3,
        exercise_type="guided_paragraph",
        label="Guided paragraph",
        objective="Write one focused paragraph with a topic sentence and supporting details.",
        min_sentences=5,
        max_sentences=8,
        min_words=70,
        max_words=120,
        sentence_frames=(
            "The main reason is ...",
            "One example of this is ...",
            "Therefore, ...",
        ),
    ),
    "consolidation": WritingLevelConfig(
        level=4,
        exercise_type="structured_response",
        label="Structured response",
        objective="Organise an introduction, a developed body paragraph, and a conclusion.",
        min_sentences=8,
        max_sentences=12,
        min_words=120,
        max_words=180,
        sentence_frames=(
            "This response will explain ...",
            "A key point is ...",
            "In conclusion, ...",
        ),
    ),
}


def writing_level_config(phase: str, task_type: str | None = None) -> WritingLevelConfig:
    if phase in _PHASE_CONFIGS:
        return _PHASE_CONFIGS[phase]

    is_task1 = task_type == "task1"
    if phase == "peak_performance":
        return WritingLevelConfig(
            level=6,
            exercise_type="exam_simulation",
            label="Timed exam practice",
            objective="Complete the task independently under realistic exam conditions.",
            min_sentences=8 if is_task1 else 12,
            max_sentences=16 if is_task1 else 24,
            min_words=140 if is_task1 else 230,
            max_words=190 if is_task1 else 290,
            show_ielts_band=True,
        )

    return WritingLevelConfig(
        level=5,
        exercise_type="ielts_task1" if is_task1 else "ielts_task2",
        label="Full IELTS task",
        objective=(
            "Summarise the key features and comparisons in a complete Academic Task 1 response."
            if is_task1
            else "Present and support a clear position in a complete Task 2 essay."
        ),
        min_sentences=8 if is_task1 else 12,
        max_sentences=16 if is_task1 else 24,
        min_words=140 if is_task1 else 230,
        max_words=190 if is_task1 else 290,
        sentence_frames=(
            ("Overall, ...", "The most noticeable feature is ...")
            if is_task1
            else ("In my view, ...", "A clear example of this is ...", "In conclusion, ...")
        ),
        show_ielts_band=True,
    )


def is_developmental_exercise(exercise_type: str | None) -> bool:
    return exercise_type in {
        "sentence_building",
        "sentence_expansion",
        "guided_paragraph",
        "structured_response",
    }
