from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class OnboardingIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=160)
    role: str = Field(pattern="^(student|lab_professional|educator)$")
    interests: list[str] = Field(default_factory=list, max_length=20)


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    body: str = Field(default="", max_length=100_000)


class CaseIn(BaseModel):
    case_code: str = Field(min_length=1, max_length=100)
    summary: str = Field(default="", max_length=20_000)
    patient_identity: str | None = Field(default=None, max_length=500)


class ResultIn(BaseModel):
    catalog_entry_id: int | None = None
    test_name: str = Field(min_length=1, max_length=200)
    value: str = Field(min_length=1, max_length=300)
    unit: str = Field(default="", max_length=80)
    reference_range: str = Field(default="", max_length=200)
    status: str = Field(default="", max_length=60)
    observed_at: datetime | None = None
    notes: str = Field(default="", max_length=10_000)


class ImportConfirmIn(BaseModel):
    upload_id: int
    results: list[ResultIn] = Field(min_length=1, max_length=500)


class ShareIn(BaseModel):
    email: str
    role: str = Field(pattern="^(view|edit|manage)$")


class SourceIn(BaseModel):
    url: HttpUrl


class QuestionIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=10_000)
    options: list[str] = Field(min_length=2, max_length=8)
    answer_index: int = Field(ge=0)
    explanation: str = Field(default="", max_length=10_000)
    topic: str = Field(default="General", max_length=160)


class CourseLessonEditIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    body: str = Field(min_length=1, max_length=100_000)
    objectives_text: str = Field(default="", max_length=10_000)
    key_terms_text: str = Field(default="", max_length=2_000)


class AttemptIn(BaseModel):
    answer_index: int = Field(ge=0)


class ContentSubmissionIn(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    body: str = Field(min_length=1, max_length=100_000)
    kind: str = Field(default="lesson", pattern="^(lesson|question)$")


class AIConversationIn(BaseModel):
    kind: str = Field(default="study", pattern="^(study|lab)$")
    note_ids: list[int] = Field(default_factory=list, max_length=20)
    upload_ids: list[int] = Field(default_factory=list, max_length=20)
    source_ids: list[int] = Field(default_factory=list, max_length=20)
    case_id: int | None = None


class AIMessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=12_000)


class InstitutionIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email_domain: str | None = Field(default=None, max_length=200)


class MemberIn(BaseModel):
    email: str
    role: str = Field(default="member", pattern="^(member|admin)$")


class TopicIn(BaseModel):
    topic: str = Field(min_length=1, max_length=300)


class WorkspaceInstitutionIn(BaseModel):
    institution_id: int
