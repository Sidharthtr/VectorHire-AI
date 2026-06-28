"""
Backwards-compatibility shim that re-exports central resume schemas.

What it does:
- Re-exports ParsedResume, Education, WorkExperience, Project from app.schemas.resume_schema
- Lets older code keep importing `app.resume.schemas` after the schemas were centralised
- Owns no logic — pure re-export module

Upstream (who imports this): legacy callers that still reference app.resume.schemas
Downstream (what this imports): app.schemas.resume_schema (the real source of truth)
"""
# Re-export from central schemas for backwards compatibility
# Pydantic resume models centralised under app/schemas/ — re-exported here for legacy paths
from app.schemas.resume_schema import ParsedResume, Education, WorkExperience, Project

__all__ = ["ParsedResume", "Education", "WorkExperience", "Project"]
