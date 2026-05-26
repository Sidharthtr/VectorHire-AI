"""
generate_resumes.py — Generate 5 realistic dummy resume PDFs using reportlab.

Run this once to create test resume PDFs:
  cd backend
  python ../scripts/generate_resumes.py

Generated files go to: backend/app/data/resumes/
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER

OUTPUT_DIR = Path(__file__).parent.parent / "backend" / "app" / "data" / "resumes"

RESUMES = [
    {
        "filename": "resume_1_alex_chen.pdf",
        "name": "Alex Chen",
        "email": "alex.chen@email.com",
        "phone": "+1 (415) 555-0101",
        "location": "San Francisco, CA",
        "summary": "Computer Science graduate student at UC Berkeley specializing in AI/ML systems. Experienced in building RAG pipelines, LLM integrations, and backend APIs using Python and FastAPI. Passionate about production AI infrastructure and agentic workflows.",
        "skills": ["Python", "FastAPI", "LangChain", "LangGraph", "ChromaDB", "Pinecone", "sentence-transformers", "Gemini API", "OpenAI API", "Docker", "Git", "RAG", "embeddings", "PostgreSQL", "React", "TypeScript"],
        "education": [
            ("UC Berkeley", "M.S. Computer Science — AI/ML Track", "Expected May 2025", "GPA: 3.9/4.0"),
            ("UCLA", "B.S. Computer Science", "May 2023", "GPA: 3.7/4.0"),
        ],
        "experience": [
            {
                "role": "AI/ML Engineering Intern",
                "company": "Anthropic",
                "dates": "Jun 2024 – Aug 2024",
                "bullets": [
                    "Built a RAG pipeline using LangChain and Pinecone for internal document search, reducing query latency by 40%",
                    "Implemented embedding generation service using sentence-transformers with batch processing",
                    "Contributed to prompt engineering library used by 15+ internal teams",
                ]
            },
            {
                "role": "Backend Engineering Intern",
                "company": "Scale AI",
                "dates": "May 2023 – Aug 2023",
                "bullets": [
                    "Built FastAPI microservices for data labeling pipeline handling 10K+ annotations/day",
                    "Designed PostgreSQL schemas for ML training data storage and retrieval",
                    "Integrated OpenAI API for automated quality checks on labeled data",
                ]
            },
        ],
        "projects": [
            ("VectorSearch Engine", "Built a semantic search system from scratch using all-MiniLM-L6-v2 embeddings and ChromaDB. Implemented cosine similarity ranking and metadata filtering. FastAPI backend with Next.js frontend.", "Python, FastAPI, ChromaDB, sentence-transformers, Next.js"),
            ("LangGraph Multi-Agent System", "Designed a supervisor-worker agent architecture using LangGraph for automated research tasks. Agents use tool calls to search the web, summarize documents, and generate reports.", "Python, LangGraph, LangChain, Gemini API, FastAPI"),
        ],
        "certs": ["Google Cloud Professional ML Engineer (2024)", "DeepLearning.AI LangChain Specialization"]
    },
    {
        "filename": "resume_2_priya_sharma.pdf",
        "name": "Priya Sharma",
        "email": "priya.sharma@gmail.com",
        "phone": "+91 98765 43210",
        "location": "Bangalore, India (Open to Remote)",
        "summary": "Recent CS graduate from IIT Bombay with strong foundation in machine learning and NLP. Built multiple production AI projects including a RAG-based Q&A system and LLMOps monitoring dashboard. Seeking entry-level AI engineering roles.",
        "skills": ["Python", "PyTorch", "transformers", "Hugging Face", "sentence-transformers", "LangChain", "FastAPI", "ChromaDB", "Docker", "AWS", "MLflow", "Git", "scikit-learn", "pandas", "numpy", "SQL"],
        "education": [
            ("IIT Bombay", "B.Tech Computer Science and Engineering", "May 2024", "CGPA: 9.1/10"),
        ],
        "experience": [
            {
                "role": "Machine Learning Research Intern",
                "company": "Samsung Research India",
                "dates": "May 2023 – Jul 2023",
                "bullets": [
                    "Fine-tuned BERT model for intent classification achieving 94% accuracy on proprietary dataset",
                    "Built data preprocessing pipeline handling 500K+ text samples using pandas and spacy",
                    "Deployed model serving API using FastAPI and Docker, integrated into production mobile app",
                ]
            },
        ],
        "projects": [
            ("RAG Q&A System", "Built a document Q&A system using LangChain, ChromaDB, and Gemini API. Implemented chunking strategies, metadata filtering, and streaming responses. Deployed on AWS EC2.", "Python, LangChain, ChromaDB, Gemini, FastAPI, AWS"),
            ("LLMOps Dashboard", "Created monitoring dashboard for LLM applications tracking cost, latency, and quality metrics. Integrated with LangSmith for trace visualization.", "Python, FastAPI, LangSmith, React, Docker"),
            ("NLP Text Classifier", "Fine-tuned DistilBERT for multi-label news classification using Hugging Face. Achieved 91% F1 score, deployed with TorchServe.", "Python, PyTorch, Hugging Face, TorchServe"),
        ],
        "certs": ["AWS Certified Cloud Practitioner", "Hugging Face NLP Course Certificate", "DeepLearning.AI MLOps Specialization"]
    },
    {
        "filename": "resume_3_james_wilson.pdf",
        "name": "James Wilson",
        "email": "james.wilson@protonmail.com",
        "phone": "+1 (312) 555-0187",
        "location": "Chicago, IL (Remote Preferred)",
        "summary": "Self-taught AI engineer with 1.5 years of professional experience building LLM-powered products. Specializes in agentic workflows, vector search, and prompt engineering. Previously a software engineer who pivoted into AI/ML engineering.",
        "skills": ["Python", "LangGraph", "LangChain", "FastAPI", "ChromaDB", "Weaviate", "Gemini", "OpenAI", "prompt engineering", "agentic AI", "JavaScript", "TypeScript", "Next.js", "PostgreSQL", "Docker", "Linux"],
        "education": [
            ("University of Illinois Chicago", "B.S. Software Engineering", "May 2022", "GPA: 3.5/4.0"),
        ],
        "experience": [
            {
                "role": "AI Engineer",
                "company": "StartupAI (early-stage)",
                "dates": "Feb 2023 – Present",
                "bullets": [
                    "Built the core RAG pipeline powering document search across 50K+ legal documents using LangChain and Weaviate",
                    "Designed LangGraph agentic workflows for automated contract review, reducing review time by 60%",
                    "Implemented prompt versioning system allowing A/B testing of prompts in production",
                    "Built full-stack features with FastAPI backend and Next.js frontend",
                ]
            },
            {
                "role": "Software Engineer",
                "company": "Accenture",
                "dates": "Jul 2022 – Jan 2023",
                "bullets": [
                    "Developed REST APIs for enterprise client using Python and Django",
                    "Maintained PostgreSQL databases and wrote complex SQL queries for reporting",
                ]
            },
        ],
        "projects": [
            ("Autonomous Job Tracker Agent", "Built an AI agent using LangGraph that autonomously tracks job applications, sends follow-up emails, and updates a Notion database. Uses browser-use for web scraping.", "Python, LangGraph, Gemini API, FastAPI, browser-use"),
            ("Semantic Code Search", "Vector search engine for codebases using code-specific embeddings. Indexes GitHub repos and enables semantic search across code snippets.", "Python, ChromaDB, sentence-transformers, FastAPI, Next.js"),
        ],
        "certs": ["LangChain Certified Developer", "Coursera Deep Learning Specialization"]
    },
    {
        "filename": "resume_4_sarah_kim.pdf",
        "name": "Sarah Kim",
        "email": "sarah.kim@outlook.com",
        "phone": "+1 (206) 555-0234",
        "location": "Seattle, WA",
        "summary": "CS sophomore at University of Washington pursuing an AI/ML concentration. Strong academic background in algorithms and machine learning. Built personal AI projects using Python, FastAPI, and LangChain. Seeking AI/ML engineering internship for Summer 2025.",
        "skills": ["Python", "FastAPI", "LangChain", "ChromaDB", "sentence-transformers", "scikit-learn", "PyTorch", "pandas", "numpy", "Git", "JavaScript", "React", "SQL", "Linux"],
        "education": [
            ("University of Washington", "B.S. Computer Science — AI/ML Concentration", "Expected May 2027", "GPA: 3.8/4.0"),
        ],
        "experience": [
            {
                "role": "Undergraduate Research Assistant",
                "company": "UW Allen School AI Lab",
                "dates": "Sep 2024 – Present",
                "bullets": [
                    "Implement NLP experiments for research on hallucination detection in LLMs",
                    "Build evaluation pipelines using Python and Hugging Face to benchmark model outputs",
                    "Maintain research code repository with 1,500+ lines of Python",
                ]
            },
        ],
        "projects": [
            ("Personal Career Copilot", "Built a RAG-powered career advice chatbot using FastAPI, ChromaDB, and Gemini API. Parses resumes with PyMuPDF and provides personalized job recommendations.", "Python, FastAPI, ChromaDB, Gemini, PyMuPDF, sentence-transformers"),
            ("Sentiment Analysis API", "Deployed a fine-tuned DistilBERT model as a REST API for real-time sentiment analysis. Handles 100+ requests/second with caching.", "Python, PyTorch, Hugging Face, FastAPI, Redis"),
        ],
        "certs": ["Google AI Essentials Certificate", "Coursera Machine Learning Specialization (Andrew Ng)"]
    },
    {
        "filename": "resume_5_omar_hassan.pdf",
        "name": "Omar Hassan",
        "email": "omar.hassan@gmail.com",
        "phone": "+44 7700 900123",
        "location": "London, UK (Open to Remote)",
        "summary": "ML Infrastructure Engineer with 2 years of experience building scalable ML training and serving systems. Expert in MLOps practices, LLMOps tooling, and cloud infrastructure for AI systems. Experienced with AWS SageMaker, vLLM, and LoRA fine-tuning workflows.",
        "skills": ["Python", "PyTorch", "Docker", "Kubernetes", "AWS", "GCP", "MLflow", "LangSmith", "vLLM", "LoRA", "fine-tuning", "FastAPI", "Terraform", "GitHub Actions", "CI/CD", "Linux", "bash", "Prometheus", "Grafana"],
        "education": [
            ("Imperial College London", "M.Eng. Computer Science", "Jun 2022", "First Class Honours"),
        ],
        "experience": [
            {
                "role": "ML Infrastructure Engineer",
                "company": "Wayve (Autonomous Driving AI)",
                "dates": "Sep 2022 – Present",
                "bullets": [
                    "Built LLM serving infrastructure using vLLM on AWS EC2 G5 instances, achieving 3x throughput improvement",
                    "Designed LoRA fine-tuning pipelines for domain adaptation of Llama models on proprietary data",
                    "Implemented LLM observability system tracking cost, latency, and quality using custom LangSmith integration",
                    "Built CI/CD pipelines for model deployment using GitHub Actions and Kubernetes, reducing deployment time by 70%",
                    "Created Terraform modules for reproducible ML infrastructure across dev/staging/prod environments",
                ]
            },
        ],
        "projects": [
            ("LLMOps Monitoring Platform", "Open-source LLMOps dashboard built with FastAPI and React. Tracks LLM API costs, latency percentiles, and quality degradation in real-time.", "Python, FastAPI, React, LangSmith, Prometheus, Grafana"),
            ("Distributed Model Fine-Tuning", "Built distributed LoRA fine-tuning system supporting multi-GPU training on AWS. Achieves 4x speedup vs single-GPU baseline.", "Python, PyTorch, LoRA, AWS, DeepSpeed"),
        ],
        "certs": ["AWS Certified Solutions Architect", "Certified Kubernetes Administrator (CKA)", "NVIDIA Deep Learning Institute Certificate"]
    }
]


def build_styles():
    styles = getSampleStyleSheet()
    name_style = ParagraphStyle("Name", fontSize=18, fontName="Helvetica-Bold", textColor=colors.HexColor("#1a1a2e"), alignment=TA_CENTER, spaceAfter=4)
    contact_style = ParagraphStyle("Contact", fontSize=9, fontName="Helvetica", textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceAfter=2)
    section_style = ParagraphStyle("Section", fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#1a1a2e"), spaceBefore=10, spaceAfter=3)
    body_style = ParagraphStyle("Body", fontSize=9.5, fontName="Helvetica", leading=13, spaceAfter=2)
    bullet_style = ParagraphStyle("Bullet", fontSize=9.5, fontName="Helvetica", leading=13, leftIndent=12, spaceAfter=1)
    subheading_style = ParagraphStyle("Subheading", fontSize=10, fontName="Helvetica-Bold", spaceAfter=1)
    return name_style, contact_style, section_style, body_style, bullet_style, subheading_style


def build_resume_pdf(resume_data: dict, output_path: Path):
    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    name_style, contact_style, section_style, body_style, bullet_style, subheading_style = build_styles()
    story = []

    # Header
    story.append(Paragraph(resume_data["name"], name_style))
    story.append(Paragraph(
        f"{resume_data['email']}  |  {resume_data['phone']}  |  {resume_data['location']}",
        contact_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a1a2e")))
    story.append(Spacer(1, 6))

    # Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
    story.append(Paragraph(resume_data["summary"], body_style))
    story.append(Spacer(1, 4))

    # Skills
    story.append(Paragraph("TECHNICAL SKILLS", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 3))
    story.append(Paragraph("  •  ".join(resume_data["skills"]), body_style))

    # Education
    story.append(Paragraph("EDUCATION", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    for inst, degree, dates, gpa in resume_data["education"]:
        story.append(Spacer(1, 3))
        story.append(Paragraph(f"<b>{inst}</b>  —  {degree}", subheading_style))
        story.append(Paragraph(f"{dates}  |  {gpa}", body_style))

    # Experience
    story.append(Paragraph("EXPERIENCE", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    for exp in resume_data["experience"]:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>{exp['role']}</b>  —  {exp['company']}  |  {exp['dates']}", subheading_style))
        for bullet in exp["bullets"]:
            story.append(Paragraph(f"• {bullet}", bullet_style))

    # Projects
    story.append(Paragraph("PROJECTS", section_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    for name, desc, tech in resume_data["projects"]:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>{name}</b>", subheading_style))
        story.append(Paragraph(desc, body_style))
        story.append(Paragraph(f"<i>Tech: {tech}</i>", body_style))

    # Certifications
    if resume_data.get("certs"):
        story.append(Paragraph("CERTIFICATIONS", section_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 3))
        for cert in resume_data["certs"]:
            story.append(Paragraph(f"• {cert}", bullet_style))

    doc.build(story)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("VectorHire AI — Resume PDF Generator")
    print("=" * 40)

    for resume in RESUMES:
        output_path = OUTPUT_DIR / resume["filename"]
        build_resume_pdf(resume, output_path)
        print(f"  ✓ Generated: {resume['filename']}  ({resume['name']})")

    print(f"\n✓ All {len(RESUMES)} resumes generated in:")
    print(f"  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
