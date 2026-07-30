from fastapi import FastAPI

from app.routers.access_protection import router as auth_router
from app.routers.mistake import router as mistake_router
from app.routers.practice_result import router as practice_result_router
from app.routers.study_plan import router as study_plan_router
from app.routers.vocabulary import router as vocabulary_router
from app.routers.writing_coach import router as writing_coach_router
from app.routers.speaking_coach import router as speaking_coach_router
from app.routers.data_portability import router as data_portability_router
from app.routers.reading_practice import router as reading_practice_router
from app.routers.listening_practice import router as listening_practice_router

app = FastAPI(title="IELTS Learning API")
app.include_router(auth_router)
app.include_router(study_plan_router)
app.include_router(mistake_router)
app.include_router(vocabulary_router)
app.include_router(practice_result_router)
app.include_router(writing_coach_router)
app.include_router(speaking_coach_router)
app.include_router(data_portability_router)
app.include_router(reading_practice_router)
app.include_router(listening_practice_router)
