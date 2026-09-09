from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class ScanRequest(StrictModel):
    kind: Literal['message','url','phone','qr']
    text: str = Field(min_length=1, max_length=6000)
    @field_validator('text')
    @classmethod
    def not_blank(cls, value: str):
        if not value.strip():
            raise ValueError('Input cannot be blank')
        return value.strip()

class ReportRequest(StrictModel):
    scan_id: str = Field(min_length=20, max_length=80)
    consent: Literal[True]
    consent_version: Literal['2026-09-09.v1']
    category: Literal['impersonation','investment','shopping','job','other'] = 'other'
    channel: Literal['telegram','facebook','messenger','sms','web','other'] = 'other'

class ReviewRequest(StrictModel):
    status: Literal['accepted','rejected']
    reason: Literal['relevant_evidence','insufficient_evidence','duplicate','out_of_scope']

class LoginRequest(StrictModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

class MfaRequest(StrictModel):
    code: str = Field(min_length=6, max_length=6)

class StaffStatusRequest(StrictModel):
    disabled: bool
