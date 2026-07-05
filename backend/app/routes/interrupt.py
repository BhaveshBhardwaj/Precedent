"""Precedent route — POST /check-precedent.

This is the core "aha" moment of Precedent: before an engineer spends hours debugging,
we search their own history for the same symptom→alert→root_cause loop and 
interrupt them with their own past precedent.
"""

from fastapi import APIRouter
from app.db.models import CheckPrecedentRequest, PrecedentResponse
from app.cognee_client import check_precedent

router = APIRouter(tags=["precedent"])


@router.post("/check-precedent", response_model=PrecedentResponse)
async def check_for_precedent(body: CheckPrecedentRequest):
    """Check if there is a known precedent for this alert.

    Called BEFORE saving the incident. If Cognee finds similar past
    incidents, returns a precedent payload with specific past instances and
    root causes — not a generic warning.

    The frontend shows this in the PrecedentModal.
    """
    result = await check_precedent(
        symptom=body.symptom,
        alert=body.alert,
        service=body.service,
    )

    return PrecedentResponse(**result)
