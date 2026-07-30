import uuid

from sqlalchemy.orm import Session

from app.models.speaking_question import SpeakingQuestion

QUESTIONS = (
    ("11111111-1111-1111-1111-111111111111", "PART_1", "What do you enjoy doing in your free time?"),
    ("22222222-2222-2222-2222-222222222222", "PART_1", "Tell me about the place where you live."),
    ("33333333-3333-3333-3333-333333333333", "PART_2", "Describe a skill you would like to learn. You should say what it is, why you want to learn it, and how you would learn it."),
    ("44444444-4444-4444-4444-444444444444", "PART_2", "Describe a memorable journey you have taken."),
    ("55555555-5555-5555-5555-555555555555", "PART_3", "How has technology changed the way people learn new skills?"),
    ("66666666-6666-6666-6666-666666666666", "PART_3", "What should cities do to improve public transport?"),
)


def seed_questions(db: Session) -> None:
    existing = {row[0] for row in db.query(SpeakingQuestion.id).all()}
    for raw_id, part, prompt in QUESTIONS:
        question_id = uuid.UUID(raw_id)
        if question_id not in existing:
            db.add(SpeakingQuestion(id=question_id, part=part, prompt=prompt))
    db.commit()
