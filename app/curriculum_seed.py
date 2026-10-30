"""Idempotent loader for the 2026-2027 curriculum and unpublished study drafts."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .curriculum_data import ASSIGNMENTS, COURSES, REQUIREMENTS, TRACKS, lesson_drafts, question_drafts
from .models import (
    Course, CourseLesson, CoursePack, CurriculumRequirement, CurriculumTrack,
    PracticeQuestion, TrackCourse,
)


def seed_curriculum(db: Session, author_id: int | None = None) -> None:
    tracks = {}
    for slug, values in TRACKS.items():
        track = db.scalar(select(CurriculumTrack).where(CurriculumTrack.slug == slug))
        if not track:
            track = CurriculumTrack(slug=slug, **values)
            db.add(track)
            db.flush()
        tracks[slug] = track

    courses = {}
    topics_by_code = {}
    for code, title, credits, topics in COURSES:
        course = db.scalar(select(Course).where(Course.code == code))
        if not course:
            course = Course(code=code, title=title, credits=credits)
            db.add(course)
            db.flush()
        else:
            course.title, course.credits = title, credits
        courses[code] = course
        topics_by_code[code] = topics

    for slug, assignments in ASSIGNMENTS.items():
        for code, study_year, semester, category in assignments:
            link = db.scalar(select(TrackCourse).where(
                TrackCourse.track_id == tracks[slug].id, TrackCourse.course_id == courses[code].id,
            ))
            if not link:
                db.add(TrackCourse(track_id=tracks[slug].id, course_id=courses[code].id,
                                   study_year=study_year, semester=semester, category=category))
            else:
                link.study_year, link.semester, link.category = study_year, semester, category

    for slug, entries in REQUIREMENTS.items():
        for code, title, study_year, credits, category in entries:
            requirement = db.scalar(select(CurriculumRequirement).where(
                CurriculumRequirement.track_id == tracks[slug].id,
                CurriculumRequirement.code == code,
            ))
            if not requirement:
                db.add(CurriculumRequirement(track_id=tracks[slug].id, code=code, title=title,
                                              study_year=study_year, credits=credits, category=category))

    db.flush()
    for code, course in courses.items():
        pack = db.scalar(select(CoursePack).where(CoursePack.course_id == course.id))
        if pack:
            continue
        topics = topics_by_code[code]
        pack = CoursePack(
            course_id=course.id,
            status="draft",
            research_notes=(
                "Editorial draft: verify course learning outcomes, scientific accuracy, current methods, "
                "and applicable guidance before publishing. Student pages intentionally omit citations; "
                "retain private editorial references here."
            ),
        )
        db.add(pack)
        db.flush()
        for lesson in lesson_drafts(course.title, topics):
            db.add(CourseLesson(course_pack_id=pack.id, **lesson))
        for question in question_drafts(course.title, topics):
            db.add(PracticeQuestion(
                author_id=author_id, course_pack_id=pack.id, **question,
                source="curriculum_draft", published=False,
            ))
    db.flush()
