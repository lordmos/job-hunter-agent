from pydantic import BaseModel
from typing import Optional


class ParseJDResult(BaseModel):
    job_title: str
    company: Optional[str] = None
    required_skills: list[str]
    preferred_skills: Optional[list[str]] = None
    experience_years: Optional[int] = None


class ParseProfileResult(BaseModel):
    user_skills: list[str]


class ParseContext(BaseModel):
    parse_jd: Optional[ParseJDResult] = None
    parse_profile: Optional[ParseProfileResult] = None


class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list[dict]] = None


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
