"""
ingest_jobs.py — Ingest a single or all TXT job files into jobs.json.

This script reads job TXT files from data/jobs/ and merges them
with the existing jobs.json. Useful if you add new job files manually.

Usage:
  cd backend
  python ../scripts/ingest_jobs.py
"""
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.constants import JOBS_DIR


def parse_txt_job(filepath: Path) -> dict | None:
    text = filepath.read_text(encoding="utf-8")
    lines = text.strip().split("\n")

    def extract(label: str) -> str:
        for line in lines:
            if line.lower().startswith(label.lower() + ":"):
                return line.split(":", 1)[1].strip()
        return ""

    title = extract("Job Title")
    company = extract("Company")
    location = extract("Location")
    exp_level_raw = extract("Experience Level").lower()
    employment_type = extract("Employment Type").lower()
    salary = extract("Salary Range")
    skills_raw = extract("Skills")

    if not title or not company:
        return None

    if "intern" in exp_level_raw:
        exp_level = "intern"
    elif "entry" in exp_level_raw:
        exp_level = "entry"
    elif "mid" in exp_level_raw:
        exp_level = "mid"
    else:
        exp_level = "entry"

    skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    remote = "remote" in location.lower()

    job_id = "job_" + re.sub(r"[^a-z0-9]", "_", filepath.stem.lower())

    return {
        "id": job_id,
        "title": title,
        "company": company,
        "location": location,
        "experience_level": exp_level,
        "employment_type": employment_type.replace("-", "").replace(" ", "-"),
        "remote": remote,
        "salary_range": salary,
        "skills": skills,
        "description": text,
        "responsibilities": [],
        "requirements": [],
    }


def main():
    print("VectorHire AI — TXT Job File Ingester")
    print("-" * 40)

    txt_files = list(JOBS_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} TXT job files")

    existing_json = JOBS_DIR / "jobs.json"
    if existing_json.exists():
        with open(existing_json) as f:
            existing_jobs = json.load(f)
        existing_ids = {j["id"] for j in existing_jobs}
    else:
        existing_jobs = []
        existing_ids = set()

    new_jobs = []
    for f in txt_files:
        parsed = parse_txt_job(f)
        if parsed and parsed["id"] not in existing_ids:
            new_jobs.append(parsed)
            print(f"  + {f.name} → {parsed['title']} at {parsed['company']}")

    if new_jobs:
        all_jobs = existing_jobs + new_jobs
        with open(existing_json, "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Added {len(new_jobs)} new jobs. Total: {len(all_jobs)}")
    else:
        print("\nNo new jobs to add.")


if __name__ == "__main__":
    main()
