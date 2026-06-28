"""
Pydantic models for a parsed resume (the LLM's structured output target).

What it does:
- Defines Education, WorkExperience, Project sub-models with sane defaults.
- ParsedResume is the canonical schema produced by the resume parser node.
- Coerces LLM int/float values (graduation_year, gpa) into strings safely.

Upstream (who imports this): app.resume.extractor, app.resume.parser (re-export),
app.resume.schemas, app.graph.state (workflow state), app.graph.nodes.extract_skills_node,
app.schemas.response_schema, app.services.resume_service, app.services.explanation_service.
Downstream (what this imports): pydantic (BaseModel, Field, field_validator), typing.Optional.
"""
# BaseModel/Field/field_validator: declare typed schemas + custom coercion for LLM output quirks
from pydantic import BaseModel, Field, field_validator
# Optional: many resume fields can legitimately be missing (no phone, no GPA, etc.)
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
