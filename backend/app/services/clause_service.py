from sqlalchemy.orm import Session
from typing import List

from app.models.clause import Clause
from app.core.constants import ClauseType


def bulk_create_clauses(
    db: Session,
    contract_id: str,
    clauses: List[str],
) -> List[Clause]:
    clause_objects = []

    for text in clauses:
        clause_objects.append(
            Clause(
                contract_id=contract_id,
                clause_text=text,
                clause_type=ClauseType.OTHER,  # AI fills later
            )
        )

    db.bulk_save_objects(clause_objects)
    db.commit()
    return clause_objects
