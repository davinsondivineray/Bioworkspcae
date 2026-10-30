"""Seed a small reviewed question bank for local development."""
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import (
    ContentSubmission, PracticeQuestion, TestCatalogEntry, User,
)
from app.curriculum_seed import seed_curriculum


SAMPLES = [
    {
        "prompt": "Which control is most useful for detecting contamination in a PCR reaction setup?",
        "options": ["No-template control", "Positive extraction control", "Known positive control", "Internal amplification control"],
        "answer_index": 0,
        "explanation": "A no-template control contains no target template and can reveal contamination introduced during setup.",
        "topic": "Molecular biology",
    },
    {
        "prompt": "What is the primary purpose of a positive control in an assay?",
        "options": ["Confirm the assay can detect its expected target", "Measure the patient's baseline", "Set the reference interval", "Replace instrument calibration"],
        "answer_index": 0,
        "explanation": "A positive control demonstrates that the assay system can produce the expected positive result.",
        "topic": "Quality control",
    },
]

CATALOG = [
    ("GLU", "Glucose", "mmol/L"),
    ("HBA1C", "Hemoglobin A1c", "%"),
    ("CREAT", "Creatinine", "µmol/L"),
    ("UREA", "Urea", "mmol/L"),
    ("SOD", "Sodium", "mmol/L"),
    ("K", "Potassium", "mmol/L"),
    ("WBC", "White blood cell count", "10^9/L"),
    ("HGB", "Hemoglobin", "g/L"),
    ("PLT", "Platelet count", "10^9/L"),
    ("CRP", "C-reactive protein", "mg/L"),
    ("ALT", "Alanine aminotransferase", "U/L"),
    ("AST", "Aspartate aminotransferase", "U/L"),
    ("TSH", "Thyroid stimulating hormone", "mIU/L"),
    ("PCR", "PCR target", ""),
]

LESSONS = [
    ("Interpreting laboratory reference intervals", "Reference intervals depend on method, population, specimen, and laboratory validation. Record the interval supplied by the performing laboratory with each result. A result outside an interval is a signal for review, not a diagnosis by itself."),
    ("PCR controls and contamination prevention", "A no-template control can help detect contamination introduced during reaction setup. Positive and internal controls answer different questions about assay performance. Review control results, instrument flags, and local procedure before interpreting a run."),
]


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        editor = db.scalar(select(User).where(User.email == "content@bioworkspace.local"))
        if not editor:
            editor = User(email="content@bioworkspace.local", display_name="BioWorkspace Editorial Team", role="editor")
            db.add(editor)
            db.flush()
        for item in SAMPLES:
            exists = db.scalar(select(PracticeQuestion.id).where(PracticeQuestion.prompt == item["prompt"]))
            if not exists:
                db.add(PracticeQuestion(**item, source="reviewed", published=True))
        for code, name, unit in CATALOG:
            exists = db.scalar(select(TestCatalogEntry.id).where(TestCatalogEntry.code == code))
            if not exists:
                db.add(TestCatalogEntry(code=code, test_name=name, default_unit=unit))
        for title, body in LESSONS:
            exists = db.scalar(select(ContentSubmission.id).where(ContentSubmission.title == title,
                                                                  ContentSubmission.status == "published"))
            if not exists:
                db.add(ContentSubmission(author_id=editor.id, title=title, body=body, kind="lesson", status="published"))
        seed_curriculum(db, author_id=editor.id)
        db.commit()
    print("Seeded BioWorkspace sample content and unpublished course-pack drafts.")


if __name__ == "__main__":
    main()
