from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str  # "patient" or "doctor"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ExtractedValueResponse(BaseModel):
    id: int
    test_name: str
    result_value: str
    unit: Optional[str]
    reference_range: Optional[str]
    is_out_of_range: bool
    evidence_snippet: Optional[str]
    is_verified: bool
    corrected_value: Optional[str]

    class Config:
        from_attributes = True

class VerifyRequestItem(BaseModel):
    extraction_id: int
    is_verified: bool
    corrected_value: Optional[str] = None

class ReportVerifyPayload(BaseModel):
    verifications: List[VerifyRequestItem]
    clinical_notes: Optional[str] = None