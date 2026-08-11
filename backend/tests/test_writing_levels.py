from app.services.writing_levels import writing_level_config


def test_six_phases_form_a_progressive_sentence_to_exam_ladder():
    phases = [
        "foundation",
        "core_skills",
        "development",
        "consolidation",
        "exam_readiness",
        "peak_performance",
    ]
    configs = [
        writing_level_config(phase, "task2" if phase.startswith(("exam", "peak")) else None)
        for phase in phases
    ]

    assert [config.level for config in configs] == [1, 2, 3, 4, 5, 6]
    assert [config.min_sentences for config in configs] == [1, 4, 5, 8, 12, 12]
    assert configs[0].exercise_type == "sentence_building"
    assert configs[3].exercise_type == "structured_response"
    assert configs[4].exercise_type == "ielts_task2"
    assert configs[5].exercise_type == "exam_simulation"
    assert all(not config.show_ielts_band for config in configs[:4])
    assert all(config.show_ielts_band for config in configs[4:])


def test_task_one_uses_its_realistic_shorter_word_target():
    task1 = writing_level_config("exam_readiness", "task1")
    task2 = writing_level_config("exam_readiness", "task2")

    assert task1.exercise_type == "ielts_task1"
    assert task1.min_words == 140
    assert task2.min_words == 230
