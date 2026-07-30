from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_learner
from app.schemas.data_portability import ExportFailure
from app.services.data_portability import assemble_export

router = APIRouter(
    prefix="/api/data-portability",
    dependencies=[Depends(require_learner)],
)


@router.post("/export")
def export(db: Session = Depends(get_db)):
    try:
        document = assemble_export(db)
        timestamp = document.produced_at.strftime("%Y%m%dT%H%M%SZ")
        return Response(
            content=document.model_dump_json(indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="ielts-learning-export-{timestamp}.json"'
                )
            },
        )
    except Exception:
        failure = ExportFailure(
            message="The complete export could not be produced. Please retry."
        )
        return JSONResponse(status_code=503, content=failure.model_dump())
