from typing import Literal
from pydantic import BaseModel, Field

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


class Analysis(BaseModel):
    risk_level: RiskLevel
    category: str
    summary: str
    warning_signs: list[str] = Field(default_factory=list)
    do_not: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    trusted_contact_recommended: bool = False
    detail: str = ""
    technical_detail: str = ""


class TextRequest(BaseModel):
    text: str = Field(max_length=8000)


class UrlRequest(BaseModel):
    url: str = Field(max_length=2048)


class ContactRequest(BaseModel):
    name: str = Field(default="Priya", min_length=1, max_length=60)
    relationship: str = Field(default="trusted contact", min_length=1, max_length=60)
