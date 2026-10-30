import json

from cryptography.fernet import Fernet

from app.config import settings
from app.curriculum_data import COURSES
from app.curriculum_seed import seed_curriculum
from app.models import (
    AIMessage, Course, CourseLesson, CoursePack, CurriculumTrack, LessonProgress,
    PatientCase, PracticeQuestion, TestCatalogEntry, Upload,
)
from conftest import TestingSession


def headers(email="student@example.test"):
    return {"X-Dev-User": email}


def test_public_landing_has_distinct_auth_actions_and_protects_dashboard(client):
    landing = client.get("/")
    assert landing.status_code == 200
    assert 'href="/signup"' in landing.text
    assert 'href="/auth/login"' in landing.text
    assert "Sign out" not in landing.text

    signup = client.get("/signup")
    assert signup.status_code == 200
    assert 'name="full_name"' in signup.text
    assert 'name="email"' in signup.text
    assert 'name="password"' in signup.text
    assert 'name="confirm_password"' in signup.text

    login = client.get("/auth/login")
    assert login.status_code == 200
    assert 'name="email"' in login.text
    assert 'name="password"' in login.text
    assert 'action="/auth/login"' in login.text

    dashboard = client.get("/dashboard", follow_redirects=False)
    assert dashboard.status_code == 303
    assert dashboard.headers["location"] == "/"
    api_response = client.get("/api/me")
    assert api_response.status_code == 401


def test_signup_login_and_logout_use_jwt_and_hash_password(client):
    import re

    from app.models import User
    from app.security import decode_access_token, verify_password
    from conftest import TestingSession

    page = client.get("/signup")
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    signup = client.post("/auth/signup", data={
        "csrf_token": csrf,
        "full_name": "Ada Lovelace",
        "email": "Ada@example.com",
        "password": "StrongPassword9!",
        "confirm_password": "StrongPassword9!",
    }, follow_redirects=False)
    assert signup.status_code == 303
    assert signup.headers["location"] == "/onboarding"
    cookie = signup.cookies.get("bioworkspace_token")
    assert cookie and decode_access_token(cookie)
    assert client.get("/api/me").status_code == 200
    with TestingSession() as db:
        user = db.query(User).filter_by(email="ada@example.com").one()
        assert user.password_hash != "StrongPassword9!"
        assert verify_password("StrongPassword9!", user.password_hash)
        assert not verify_password("IncorrectPassword9!", user.password_hash)

    client.post("/auth/logout", follow_redirects=False)
    page = client.get("/auth/login")
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    login = client.post("/auth/login", data={
        "csrf_token": csrf,
        "email": "ADA@example.com",
        "password": "StrongPassword9!",
    }, follow_redirects=False)
    assert login.status_code == 303
    assert login.headers["location"] == "/dashboard"
    assert client.get("/api/me").status_code == 200

    client.post("/auth/logout", follow_redirects=False)
    assert client.get("/api/me").status_code == 401


def test_signup_rejects_password_mismatch(client):
    import re

    page = client.get("/signup")
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    response = client.post("/auth/signup", data={
        "csrf_token": csrf,
        "full_name": "Ada Lovelace",
        "email": "ada@example.com",
        "password": "StrongPassword9!",
        "confirm_password": "DifferentPassword9!",
    })
    assert response.status_code == 400
    assert "passwords do not match" in response.text


def test_curriculum_seed_is_idempotent_and_deduplicates_shared_courses():
    with TestingSession() as db:
        seed_curriculum(db)
        db.commit()
        first = (
            db.query(CurriculumTrack).count(), db.query(Course).count(),
            db.query(CoursePack).count(), db.query(CourseLesson).count(),
            db.query(PracticeQuestion).filter(PracticeQuestion.course_pack_id.is_not(None)).count(),
        )
        seed_curriculum(db)
        db.commit()
        second = (
            db.query(CurriculumTrack).count(), db.query(Course).count(),
            db.query(CoursePack).count(), db.query(CourseLesson).count(),
            db.query(PracticeQuestion).filter(PracticeQuestion.course_pack_id.is_not(None)).count(),
        )
        shared = db.query(Course).filter_by(code="2019020").one()
        assert db.query(CurriculumTrack).count() == 2
        assert len(shared.course_links) == 2
        assert all(len(pack.lessons) == 6 and len(pack.questions) == 20 for pack in db.query(CoursePack).all())
        assert first == second
        assert second[1] == len(COURSES)


def test_course_catalog_hides_drafts_until_editor_publishes(client, monkeypatch):
    with TestingSession() as db:
        seed_curriculum(db)
        db.commit()
        course = db.query(Course).filter_by(code="2019020").one()
        pack = db.query(CoursePack).filter_by(course_id=course.id).one()
        pack_id = pack.id
        lesson_id = pack.lessons[0].id

    catalog = client.get("/api/curriculum", headers=headers()).json()
    assert len(catalog) == 2
    shared_memberships = [
        any(course["code"] == "2019020" for year in track["years"] for course in year["courses"])
        for track in catalog
    ]
    assert shared_memberships == [True, True]
    assert "Final Test" in [item["title"] for track in catalog for item in track["requirements"]]

    hidden = client.get("/courses/2019020", headers=headers())
    assert hidden.status_code == 200
    assert "Course pack in editorial review" in hidden.text
    assert "This draft lesson introduces" not in hidden.text
    assert "private editorial references" not in hidden.text

    monkeypatch.setattr(settings, "editor_emails", "editor@example.test")
    review = client.get("/editor", headers=headers("editor@example.test"))
    assert review.status_code == 200
    assert "Course packs awaiting review" in review.text
    assert "private editorial references" in review.text
    published = client.post(f"/api/editor/course-packs/{pack_id}/publish", headers=headers("editor@example.test"))
    assert published.status_code == 200
    assert published.json()["status"] == "published"

    visible = client.get("/courses/2019020", headers=headers())
    assert visible.status_code == 200
    assert "This draft lesson introduces" in visible.text
    assert "course review questions" in visible.text.lower()
    assert "private editorial references" not in visible.text
    assert "medical-biotechnologies.unisi.it" not in visible.text
    marked = client.post(f"/api/courses/2019020/lessons/{lesson_id}/complete", headers=headers())
    assert marked.status_code == 200
    with TestingSession() as db:
        assert db.query(LessonProgress).filter_by(lesson_id=lesson_id).count() == 1


def test_health_dashboard_and_onboarding(client):
    assert client.get("/health").json()["status"] == "ok"
    response = client.get("/dashboard", headers=headers())
    assert response.status_code == 200
    result = client.post("/api/onboarding", headers=headers(), json={
        "display_name": "A Student", "role": "student", "interests": ["Genetics"],
    })
    assert result.status_code == 200
    assert client.get("/api/me", headers=headers()).json()["interests"] == ["Genetics"]


def test_notes_are_private_to_the_owner(client):
    created = client.post("/api/notes", headers=headers(), json={"title": "PCR", "body": "Controls and primers"})
    assert created.status_code == 201
    assert client.get("/api/notes", headers=headers()).json()[0]["title"] == "PCR"
    assert client.get("/api/notes", headers=headers("other@example.test")).json() == []
    hidden = client.put(f"/api/notes/{created.json()['id']}", headers=headers("other@example.test"),
                        json={"title": "Changed", "body": "No access"})
    assert hidden.status_code == 404


def test_case_sharing_enforces_view_and_edit_permissions(client):
    case = client.post("/api/cases", headers=headers(), json={"case_code": "CASE-001", "summary": "QC review"})
    assert case.status_code == 201
    case_id = case.json()["id"]
    client.get("/api/me", headers=headers("colleague@example.test"))
    shared = client.post(f"/api/cases/{case_id}/share", headers=headers(),
                         json={"email": "colleague@example.test", "role": "view"})
    assert shared.status_code == 201
    assert client.get(f"/api/cases/{case_id}", headers=headers("colleague@example.test")).status_code == 200
    denied = client.post(f"/api/cases/{case_id}/results", headers=headers("colleague@example.test"),
                         json={"test_name": "Glucose", "value": "5.1"})
    assert denied.status_code == 404
    client.post(f"/api/cases/{case_id}/share", headers=headers(),
                json={"email": "colleague@example.test", "role": "edit"})
    allowed = client.post(f"/api/cases/{case_id}/results", headers=headers("colleague@example.test"),
                          json={"test_name": "Glucose", "value": "5.1", "unit": "mmol/L"})
    assert allowed.status_code == 201
    assert client.get(f"/api/cases/{case_id}", headers=headers()).json()["results"][0]["value"] == "5.1"


def test_catalog_suggests_common_tests_without_overriding_local_ranges(client):
    with TestingSession() as db:
        db.add(TestCatalogEntry(code="GLU", test_name="Glucose", default_unit="mmol/L"))
        db.commit()
    catalog = client.get("/api/test-catalog", params={"q": "gluc"})
    assert catalog.json()[0]["test_name"] == "Glucose"
    case = client.post("/api/cases", headers=headers(), json={"case_code": "CASE-CAT"}).json()
    result = client.post(f"/api/cases/{case['id']}/results", headers=headers(), json={
        "test_name": "Glucose", "value": "5.4", "unit": "mmol/L", "reference_range": "4.1–5.9 local",
    })
    assert result.status_code == 201
    case_data = client.get(f"/api/cases/{case['id']}", headers=headers()).json()
    assert case_data["results"][0]["catalog_entry_id"] == 1
    assert case_data["results"][0]["reference_range"] == "4.1–5.9 local"


def test_identifiable_records_are_blocked_by_default(client):
    denied_mode = client.put("/api/workspace/identity-mode", headers=headers(), data={"mode": "identifiable"})
    assert denied_mode.status_code == 403
    denied_identity = client.post("/api/cases", headers=headers(), json={
        "case_code": "CASE-002", "patient_identity": "Jane Doe",
    })
    assert denied_identity.status_code == 403


def test_identifiable_identity_is_encrypted_when_privacy_gate_is_enabled(client, monkeypatch):
    monkeypatch.setattr(settings, "identifiable_records_enabled", True)
    monkeypatch.setattr(settings, "patient_field_encryption_key", Fernet.generate_key().decode())
    changed = client.put("/api/workspace/identity-mode", headers=headers(), data={"mode": "identifiable"})
    assert changed.status_code == 200
    response = client.post("/api/cases", headers=headers(), json={
        "case_code": "CASE-PRIVATE", "patient_identity": "Jane Doe",
    })
    assert response.status_code == 201
    assert response.json()["patient_identity"] == "Jane Doe"
    with TestingSession() as db:
        record = db.query(PatientCase).filter_by(case_code="CASE-PRIVATE").one()
        assert record.patient_identity_ciphertext != "Jane Doe"


def test_upload_import_requires_review_before_structured_save(client):
    case = client.post("/api/cases", headers=headers(), json={"case_code": "CASE-CSV"}).json()
    upload = client.post("/api/cases/import", headers=headers(), data={"case_id": str(case["id"])},
                         files={"file": ("results.csv", b"Test,Result,Unit\nGlucose,5.2,mmol/L\n", "text/csv")})
    assert upload.status_code == 202
    upload_id = upload.json()["upload_id"]
    with TestingSession() as db:
        record = db.get(Upload, upload_id)
        record.status = "ready"
        record.extracted_text = "Test,Result,Unit\nGlucose,5.2,mmol/L\n"
        record.extracted_rows = [{"Test": "Glucose", "Result": "5.2", "Unit": "mmol/L"}]
        db.commit()
    preview = client.get(f"/api/cases/{case['id']}/import-preview", headers=headers(), params={"upload_id": upload_id})
    assert preview.status_code == 200
    assert preview.json()["rows"][0]["Test"] == "Glucose"
    confirm = client.post(f"/api/cases/{case['id']}/import-confirm", headers=headers(), json={
        "upload_id": upload_id,
        "results": [{"test_name": "Glucose", "value": "5.2", "unit": "mmol/L"}],
    })
    assert confirm.status_code == 201
    assert confirm.json()["created"] == 1


def test_disabled_ai_does_not_block_workspace_and_returns_clear_error(client):
    note = client.post("/api/notes", headers=headers(), json={"title": "Study note", "body": "PCR"}).json()
    conversation = client.post("/api/ai/conversations", headers=headers(), json={"kind": "study", "note_ids": [note["id"]]})
    assert conversation.status_code == 201
    response = client.post(f"/api/ai/conversations/{conversation.json()['id']}/messages", headers=headers(),
                           json={"content": "Explain this note"})
    assert response.status_code == 503
    assert client.get("/api/notes", headers=headers()).status_code == 200


def test_ai_quota_is_enforced_per_user(client, monkeypatch):
    monkeypatch.setattr(settings, "ai_monthly_request_limit", 0)
    note = client.post("/api/notes", headers=headers(), json={"title": "Study note", "body": "PCR"}).json()
    conversation = client.post("/api/ai/conversations", headers=headers(), json={"kind": "study", "note_ids": [note["id"]]}).json()
    response = client.post(f"/api/ai/conversations/{conversation['id']}/messages", headers=headers(),
                           json={"content": "Explain"})
    assert response.status_code == 429


def test_ai_receives_selected_context_with_identifier_redaction(client, monkeypatch):
    from app.ai import provider

    captured = {}

    async def fake_complete(messages):
        captured["messages"] = messages
        return "PCR amplification is monitored with controls."

    monkeypatch.setattr(provider, "complete", fake_complete)
    note = client.post("/api/notes", headers=headers(), json={
        "title": "Lab note", "body": "MRN: 123456; contact jane@example.org",
    }).json()
    conversation = client.post("/api/ai/conversations", headers=headers(), json={
        "kind": "study", "note_ids": [note["id"]],
    }).json()
    response = client.post(f"/api/ai/conversations/{conversation['id']}/messages", headers=headers(),
                           json={"content": "Please explain this for jane@example.org"})
    assert response.status_code == 200
    sent_text = json.dumps(captured["messages"])
    assert "jane@example.org" not in sent_text
    assert "123456" not in sent_text
    assert response.json()["citations"][0]["label"] == "Lab note"
    with TestingSession() as db:
        saved_user_message = db.query(AIMessage).filter_by(role="user").one()
        assert "jane@example.org" not in saved_user_message.content


def test_lab_ai_is_only_available_to_lab_professionals(client, monkeypatch):
    role = client.post("/api/onboarding", headers=headers(), json={
        "display_name": "Professional", "role": "lab_professional", "interests": [],
    })
    assert role.status_code == 200
    case = client.post("/api/cases", headers=headers(), json={"case_code": "CASE-QC", "summary": "QC control failed"}).json()
    result = client.post(f"/api/cases/{case['id']}/results", headers=headers(), json={
        "test_name": "Control", "value": "High", "status": "QC flag",
    })
    assert result.status_code == 201
    response = client.post("/api/ai/conversations", headers=headers(), json={"kind": "lab", "case_id": case["id"]})
    assert response.status_code == 201

    from app.ai import provider
    sent = {}
    async def fake_complete(messages):
        sent["messages"] = messages
        return "Check the control material, lot, calibration, and instrument flags."
    monkeypatch.setattr(provider, "complete", fake_complete)
    answer = client.post(f"/api/ai/conversations/{response.json()['id']}/messages", headers=headers(),
                         json={"content": "What technical checks should I make?"})
    assert answer.status_code == 200
    assert "do not diagnose" in sent["messages"][0]["content"].lower()


def test_institution_domain_request_and_admin_approval(client):
    created = client.post("/api/institutions", headers=headers("admin@lab.example.test"), json={
        "name": "Example Lab", "email_domain": "lab.example.test",
    })
    institution_id = created.json()["id"]
    assert created.status_code == 201
    request = client.post(f"/api/institutions/{institution_id}/request", headers=headers("staff@lab.example.test"))
    assert request.status_code == 201
    members = client.get(f"/api/institutions/{institution_id}/members", headers=headers("admin@lab.example.test"))
    request_id = members.json()["requests"][0]["id"]
    approved = client.post(f"/api/institutions/{institution_id}/requests/{request_id}/approve",
                           headers=headers("admin@lab.example.test"))
    assert approved.status_code == 200
    assert client.get("/api/institutions", headers=headers("staff@lab.example.test")).json()[0]["name"] == "Example Lab"


def test_account_export_and_delete(client):
    client.post("/api/notes", headers=headers(), json={"title": "Exported", "body": "my data"})
    exported = client.get("/api/account/export", headers=headers())
    assert exported.status_code == 200
    assert exported.json()["notes"][0]["title"] == "Exported"
    deleted = client.delete("/api/account", headers=headers())
    assert deleted.status_code == 204
    after = client.get("/api/notes", headers=headers())
    assert after.json() == []
