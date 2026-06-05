from pydantic import BaseModel, Field, field_validator
from typing import Optional


class Education(BaseModel):
    institution: str
    degree: str
    field: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None

    @field_validator("graduation_year", "gpa", mode="before")
    @classmethod
    def coerce_to_str(cls, v):
        # LLMs often return graduation_year as int (2022) and gpa as float (3.8).
        # Convert to string so Pydantic doesn't reject valid LLM output.
        return str(v) if v is not None else None


class WorkExperience(BaseModel):
    company: str
    role: str
    duration: str
    description: str
    skills_used: list[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str
    description: str
    technologies: list[str] = Field(default_factory=list)
    url: Optional[str] = None


class ParsedResume(BaseModel):
    raw_text: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    experience: list[WorkExperience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    years_of_experience: Optional[float] = None
    experience_level: Optional[str] = None  # intern, entry, mid, senior
