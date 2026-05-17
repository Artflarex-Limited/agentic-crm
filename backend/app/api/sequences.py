"""
Sequences API routes
"""
import json

from fastapi import APIRouter, HTTPException

from app.prisma import prisma
from app.schemas.schemas import SequenceCreate, SequenceResponse

router = APIRouter()


@router.get("/", response_model=list[SequenceResponse])
async def list_sequences():
    results = await prisma.sequence.find_many(order=[{"id": "desc"}])
    sequences = []
    for r in results:
        data = r.model_dump()
        # Deserialize JSON fields
        if data.get("steps"):
            data["steps"] = json.loads(data["steps"]) if isinstance(data["steps"], str) else data["steps"]
        sequences.append(data)
    return sequences


@router.get("/{sequence_id}", response_model=SequenceResponse)
async def get_sequence(sequence_id: int):
    seq = await prisma.sequence.find_first(where={"id": sequence_id})
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")
    data = seq.model_dump()
    if data.get("steps"):
        data["steps"] = json.loads(data["steps"]) if isinstance(data["steps"], str) else data["steps"]
    return data


@router.post("/", response_model=SequenceResponse, status_code=201)
async def create_sequence(data: SequenceCreate):
    payload = data.model_dump()
    # Serialize JSON fields
    if payload.get("steps"):
        payload["steps"] = json.dumps(payload["steps"])
    seq = await prisma.sequence.create(data=payload)
    result_data = seq.model_dump()
    if result_data.get("steps"):
        result_data["steps"] = json.loads(result_data["steps"]) if isinstance(result_data["steps"], str) else result_data["steps"]
    return result_data


@router.put("/{sequence_id}", response_model=SequenceResponse)
async def update_sequence(sequence_id: int, data: SequenceCreate):
    seq = await prisma.sequence.find_first(where={"id": sequence_id})
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")
    payload = data.model_dump()
    # Serialize JSON fields
    if payload.get("steps"):
        payload["steps"] = json.dumps(payload["steps"])
    seq = await prisma.sequence.update(where={"id": sequence_id}, data=payload)
    result_data = seq.model_dump()
    if result_data.get("steps"):
        result_data["steps"] = json.loads(result_data["steps"]) if isinstance(result_data["steps"], str) else result_data["steps"]
    return result_data


@router.delete("/{sequence_id}")
async def delete_sequence(sequence_id: int):
    seq = await prisma.sequence.find_first(where={"id": sequence_id})
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")
    await prisma.sequence.delete(where={"id": sequence_id})
    return {"deleted": True}


@router.post("/{sequence_id}/enroll/{lead_id}")
async def enroll_lead(sequence_id: int, lead_id: int):
    """Enroll a lead into a sequence"""
    # Verify lead exists
    lead = await prisma.lead.find_first(where={"id": lead_id})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    enrollment = await prisma.sequenceenrollment.create(
        data={"leadId": lead_id, "sequenceId": sequence_id}
    )
    return {"enrolled": True, "enrollment_id": enrollment.id}