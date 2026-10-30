from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    password_hash: Mapped[str | None] = mapped_column(String(300), nullable=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160), default="")
    role: Mapped[str] = mapped_column(String(40), default="student")
    interests: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    workspaces: Mapped[list["Workspace"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Institution(Base):
    __tablename__ = "institutions"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email_domain: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    memberships: Mapped[list["Membership"]] = relationship(back_populates="institution", cascade="all, delete-orphan")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("institution_id", "user_id", name="uq_membership_user"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(40), default="member")
    status: Mapped[str] = mapped_column(String(24), default="active")
    institution: Mapped[Institution] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship()


class MembershipRequest(Base):
    __tablename__ = "membership_requests"
    __table_args__ = (UniqueConstraint("institution_id", "user_id", name="uq_membership_request"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(24), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    user: Mapped[User] = relationship()


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(160), default="My workspace")
    identity_mode: Mapped[str] = mapped_column(String(24), default="pseudonymous")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    owner: Mapped[User] = relationship(back_populates="workspaces")


class PatientCase(Base):
    __tablename__ = "patient_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    case_code: Mapped[str] = mapped_column(String(100), index=True)
    patient_identity_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    results: Mapped[list["TestResult"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    shares: Mapped[list["CaseShare"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class TestCatalogEntry(Base):
    __tablename__ = "test_catalog"
    __table_args__ = (UniqueConstraint("code", name="uq_test_catalog_code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), index=True)
    test_name: Mapped[str] = mapped_column(String(200), index=True)
    default_unit: Mapped[str] = mapped_column(String(80), default="")


class TestResult(Base):
    __tablename__ = "test_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("patient_cases.id", ondelete="CASCADE"), index=True)
    catalog_entry_id: Mapped[int | None] = mapped_column(ForeignKey("test_catalog.id", ondelete="SET NULL"), nullable=True)
    test_name: Mapped[str] = mapped_column(String(200))
    value: Mapped[str] = mapped_column(String(300))
    unit: Mapped[str] = mapped_column(String(80), default="")
    reference_range: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(60), default="")
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    case: Mapped[PatientCase] = relationship(back_populates="results")


class CaseShare(Base):
    __tablename__ = "case_shares"
    __table_args__ = (UniqueConstraint("case_id", "user_id", name="uq_case_share"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("patient_cases.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16), default="view")
    case: Mapped[PatientCase] = relationship(back_populates="shares")


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class LearningSource(Base):
    __tablename__ = "learning_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(300), default="")
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(24), default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Upload(Base):
    __tablename__ = "uploads"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    note_id: Mapped[int | None] = mapped_column(ForeignKey("notes.id", ondelete="SET NULL"), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    extracted_rows: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(24), default="stored")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    object_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class PracticeQuestion(Base):
    __tablename__ = "practice_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)
    answer_index: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(Text, default="")
    topic: Mapped[str] = mapped_column(String(160), default="General")
    source: Mapped[str] = mapped_column(String(24), default="reviewed")
    course_pack_id: Mapped[int | None] = mapped_column(ForeignKey("course_packs.id", ondelete="CASCADE"), nullable=True, index=True)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    course_pack: Mapped["CoursePack | None"] = relationship(back_populates="questions")


class PracticeAttempt(Base):
    __tablename__ = "practice_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("practice_questions.id", ondelete="CASCADE"), index=True)
    answer_index: Mapped[int] = mapped_column(Integer)
    correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ContentSubmission(Base):
    __tablename__ = "content_submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    body: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(24), default="lesson")
    status: Mapped[str] = mapped_column(String(24), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AIConversation(Base):
    __tablename__ = "ai_conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20), default="study")
    selected_note_ids: Mapped[list] = mapped_column(JSON, default=list)
    selected_upload_ids: Mapped[list] = mapped_column(JSON, default=list)
    selected_source_ids: Mapped[list] = mapped_column(JSON, default=list)
    selected_case_id: Mapped[int | None] = mapped_column(ForeignKey("patient_cases.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AIMessage(Base):
    __tablename__ = "ai_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


Index("ix_cases_workspace_created", PatientCase.workspace_id, PatientCase.created_at)


class CurriculumTrack(Base):
    __tablename__ = "curriculum_tracks"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    course_links: Mapped[list["TrackCourse"]] = relationship(back_populates="track", cascade="all, delete-orphan")
    requirements: Mapped[list["CurriculumRequirement"]] = relationship(back_populates="track", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(240))
    credits: Mapped[int] = mapped_column(Integer, default=0)
    course_links: Mapped[list["TrackCourse"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    pack: Mapped["CoursePack | None"] = relationship(back_populates="course", cascade="all, delete-orphan", uselist=False)


class TrackCourse(Base):
    __tablename__ = "track_courses"
    __table_args__ = (UniqueConstraint("track_id", "course_id", name="uq_track_course"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("curriculum_tracks.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    study_year: Mapped[int] = mapped_column(Integer)
    semester: Mapped[str] = mapped_column(String(80), default="")
    category: Mapped[str] = mapped_column(String(120), default="")
    track: Mapped[CurriculumTrack] = relationship(back_populates="course_links")
    course: Mapped[Course] = relationship(back_populates="course_links")


class CurriculumRequirement(Base):
    __tablename__ = "curriculum_requirements"
    __table_args__ = (UniqueConstraint("track_id", "code", name="uq_track_requirement"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("curriculum_tracks.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(240))
    study_year: Mapped[int] = mapped_column(Integer)
    credits: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(120), default="")
    track: Mapped[CurriculumTrack] = relationship(back_populates="requirements")


class CoursePack(Base):
    __tablename__ = "course_packs"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(24), default="draft")
    research_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    course: Mapped[Course] = relationship(back_populates="pack")
    lessons: Mapped[list["CourseLesson"]] = relationship(back_populates="pack", cascade="all, delete-orphan", order_by="CourseLesson.position")
    questions: Mapped[list[PracticeQuestion]] = relationship(back_populates="course_pack", cascade="all, delete-orphan")


class CourseLesson(Base):
    __tablename__ = "course_lessons"
    __table_args__ = (UniqueConstraint("course_pack_id", "position", name="uq_course_lesson_position"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    course_pack_id: Mapped[int] = mapped_column(ForeignKey("course_packs.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(240))
    objectives: Mapped[list] = mapped_column(JSON, default=list)
    body: Mapped[str] = mapped_column(Text, default="")
    key_terms: Mapped[list] = mapped_column(JSON, default=list)
    pack: Mapped[CoursePack] = relationship(back_populates="lessons")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("course_lessons.id", ondelete="CASCADE"), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
