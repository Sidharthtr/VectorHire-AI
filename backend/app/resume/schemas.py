# Re-export from central schemas for backwards compatibility
from app.schemas.resume_schema import ParsedResume, Education, WorkExperience, Project

__all__ = ["ParsedResume", "Education", "WorkExperience", "Project"]
