"""Smoke tests for generic CRUD, and the full Strict Enrollment Policy matrix.

Test numbers in comments refer to the policy's §32 matrix (see the approved
plan at .claude/plans/todo-md-create-crud-for-linear-journal.md).
"""

import json
import uuid
from typing import Any

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase

from core.models import (
    Curriculum,
    CurriculumSubject,
    Department,
    Enrollment,
    EnrollmentStatus,
    Faculty,
    OpenClass,
    Section,
    Student,
    Subject,
    SubjectRequirementType,
    University,
)


class UniqueConstraintTests(TestCase):
    def setUp(self) -> None:
        self.university = University.objects.create(name="Test University")
        self.faculty = Faculty.objects.create(university=self.university, name="Engineering")
        self.department = Department.objects.create(faculty=self.faculty, name="CPE")
        self.curriculum = Curriculum.objects.create(
            department=self.department, name="CPE Curriculum", year=2026
        )
        self.subject = Subject.objects.create(
            department=self.department, code="CPE101", name="Intro", credit=3
        )
        self.student = Student.objects.create(
            curriculum=self.curriculum, student_code="S001", name="Alice"
        )
        self.open_class = OpenClass.objects.create(
            subject=self.subject, academic_year=2026, semester=1
        )
        self.section = Section.objects.create(
            open_class=self.open_class, section_no="1", capacity=40
        )

    def test_duplicate_curriculum_subject_rejected(self) -> None:
        CurriculumSubject.objects.create(
            curriculum=self.curriculum,
            subject=self.subject,
            type=SubjectRequirementType.CORE,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            CurriculumSubject.objects.create(
                curriculum=self.curriculum,
                subject=self.subject,
                type=SubjectRequirementType.MAJOR,
            )

    def test_duplicate_section_no_rejected(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            Section.objects.create(open_class=self.open_class, section_no="1")

    def test_duplicate_enrollment_rejected(self) -> None:
        Enrollment.objects.create(
            student=self.student, section=self.section, status=EnrollmentStatus.ENROLLED
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Enrollment.objects.create(
                student=self.student, section=self.section, status=EnrollmentStatus.WITHDRAWN
            )

    def test_subject_department_deletion_sets_subject_to_null(self) -> None:
        empty_department = Department.objects.create(faculty=self.faculty, name="Temporary")
        self.subject.department = empty_department
        self.subject.save(update_fields=["department"])

        empty_department.delete()

        self.subject.refresh_from_db()
        self.assertIsNone(self.subject.department)

    def test_curriculum_delete_is_protected_when_students_exist(self) -> None:
        Student.objects.create(
            curriculum=self.curriculum,
            student_code="S002",
            name="Bob",
        )

        with self.assertRaises(ProtectedError):
            self.curriculum.delete()

    def test_subject_delete_is_protected_when_open_class_exists(self) -> None:
        OpenClass.objects.create(
            subject=self.subject,
            academic_year=2026,
            semester=2,
        )

        with self.assertRaises(ProtectedError):
            self.subject.delete()


class CrudApiTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_swagger_docs_and_tag_groups_are_available(self) -> None:
        docs_resp = self.client.get("/api/docs")
        self.assertEqual(docs_resp.status_code, 200)
        self.assertIn("swagger", docs_resp.content.decode("utf-8").lower())

        openapi_resp = self.client.get("/api/openapi.json")
        self.assertEqual(openapi_resp.status_code, 200)

        tags = {tag["name"] for tag in openapi_resp.json().get("tags", [])}
        self.assertIn("University", tags)
        self.assertIn("Student", tags)
        self.assertIn("Enrollment", tags)

    def test_university_crud_round_trip(self) -> None:
        create_resp = self.client.post(
            "/api/universities/",
            data=json.dumps({"name": "Round Trip University"}),
            content_type="application/json",
        )
        self.assertEqual(create_resp.status_code, 200)
        university_id = create_resp.json()["id"]

        list_resp = self.client.get("/api/universities/")
        self.assertEqual(list_resp.status_code, 200)
        self.assertTrue(any(u["id"] == university_id for u in list_resp.json()))

        get_resp = self.client.get(f"/api/universities/{university_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["name"], "Round Trip University")

        put_resp = self.client.put(
            f"/api/universities/{university_id}",
            data=json.dumps({"name": "Renamed University"}),
            content_type="application/json",
        )
        self.assertEqual(put_resp.status_code, 200)
        self.assertEqual(put_resp.json()["name"], "Renamed University")

        delete_resp = self.client.delete(f"/api/universities/{university_id}")
        self.assertEqual(delete_resp.status_code, 200)

        final_get = self.client.get(f"/api/universities/{university_id}")
        self.assertEqual(final_get.status_code, 404)


class JoinClassPolicyTests(TestCase):
    """The §32 test matrix for join_class / withdraw_enrollment."""

    def setUp(self) -> None:
        self.client = Client()

        self.university = University.objects.create(name="Policy University")
        self.faculty = Faculty.objects.create(university=self.university, name="Engineering")
        self.department = Department.objects.create(faculty=self.faculty, name="CPE")
        self.curriculum = Curriculum.objects.create(
            department=self.department, name="CPE Curriculum", year=2026
        )

        # Subject in the student's curriculum.
        self.subject = Subject.objects.create(
            department=self.department, code="CPE101", name="Intro", credit=3
        )
        CurriculumSubject.objects.create(
            curriculum=self.curriculum, subject=self.subject, type=SubjectRequirementType.CORE
        )
        self.open_class = OpenClass.objects.create(
            subject=self.subject, academic_year=2026, semester=1
        )
        self.section1 = Section.objects.create(
            open_class=self.open_class, section_no="1", capacity=2
        )
        self.section2 = Section.objects.create(
            open_class=self.open_class, section_no="2", capacity=2
        )
        # Same subject, different OpenClass (different semester) -> a separate offering (§13/14).
        self.open_class_sem2 = OpenClass.objects.create(
            subject=self.subject, academic_year=2026, semester=2
        )
        self.section_sem2 = Section.objects.create(
            open_class=self.open_class_sem2, section_no="1", capacity=2
        )

        # Subject NOT in the student's curriculum.
        self.unlinked_subject = Subject.objects.create(
            department=self.department, code="MA999", name="Unlinked", credit=3
        )
        self.unlinked_open_class = OpenClass.objects.create(
            subject=self.unlinked_subject, academic_year=2026, semester=1
        )
        self.unlinked_section = Section.objects.create(
            open_class=self.unlinked_open_class, section_no="1", capacity=1
        )

        self.student = Student.objects.create(
            curriculum=self.curriculum, student_code="S001", name="Alice"
        )
        self.other_student = Student.objects.create(
            curriculum=self.curriculum, student_code="S002", name="Bob"
        )

    def join(self, section_id: Any, student_id: Any) -> Any:
        return self.client.post(
            f"/api/sections/{section_id}/join",
            data=json.dumps({"student_id": str(student_id)}),
            content_type="application/json",
        )

    def withdraw(self, enrollment_id: Any) -> Any:
        return self.client.post(f"/api/enrollments/{enrollment_id}/withdraw")

    # 01 -----------------------------------------------------------------
    def test_01_valid_join_succeeds(self) -> None:
        resp = self.join(self.section1.id, self.student.id)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "Enrolled")
        self.assertIsNone(body["grade"])

    # 02 -----------------------------------------------------------------
    def test_02_student_not_found(self) -> None:
        resp = self.join(self.section1.id, uuid.uuid4())
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["code"], "STUDENT_NOT_FOUND")

    # 03 -----------------------------------------------------------------
    def test_03_section_not_found(self) -> None:
        resp = self.join(uuid.uuid4(), self.student.id)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["code"], "SECTION_NOT_FOUND")

    # 04 -----------------------------------------------------------------
    def test_04_ineligible_and_full_returns_eligibility_error_first(self) -> None:
        # Fill the unlinked section to capacity (bypassing the service on purpose).
        Enrollment.objects.create(
            student=self.other_student,
            section=self.unlinked_section,
            status=EnrollmentStatus.ENROLLED,
        )
        resp = self.join(self.unlinked_section.id, self.student.id)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["code"], "SUBJECT_NOT_IN_CURRICULUM")

    # 05 -----------------------------------------------------------------
    def test_05_capacity_null_rejected(self) -> None:
        section = Section.objects.create(
            open_class=self.open_class, section_no="null-cap", capacity=None
        )
        resp = self.join(section.id, self.student.id)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "SECTION_CAPACITY_NOT_CONFIGURED")

    # 06 -----------------------------------------------------------------
    def test_06_capacity_zero_rejected(self) -> None:
        section = Section.objects.create(
            open_class=self.open_class, section_no="zero-cap", capacity=0
        )
        resp = self.join(section.id, self.student.id)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "SECTION_CAPACITY_NOT_CONFIGURED")

    # 07 -----------------------------------------------------------------
    def test_07_section_full_rejected(self) -> None:
        full_section = Section.objects.create(
            open_class=self.open_class, section_no="full", capacity=1
        )
        Enrollment.objects.create(
            student=self.other_student, section=full_section, status=EnrollmentStatus.ENROLLED
        )
        resp = self.join(full_section.id, self.student.id)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "SECTION_FULL")

    # 08 -----------------------------------------------------------------
    def test_08_duplicate_join_rejected(self) -> None:
        self.assertEqual(self.join(self.section1.id, self.student.id).status_code, 200)
        resp = self.join(self.section1.id, self.student.id)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "ALREADY_ENROLLED")

    # 09 -----------------------------------------------------------------
    def test_09_another_section_same_open_class_rejected(self) -> None:
        self.assertEqual(self.join(self.section1.id, self.student.id).status_code, 200)
        resp = self.join(self.section2.id, self.student.id)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "ALREADY_ENROLLED_IN_OPEN_CLASS")

    # 10 -----------------------------------------------------------------
    def test_10_withdrawn_then_join_different_section_allowed(self) -> None:
        first = self.join(self.section1.id, self.student.id).json()
        self.assertEqual(self.withdraw(first["id"]).status_code, 200)
        resp = self.join(self.section2.id, self.student.id)
        self.assertEqual(resp.status_code, 200)

    # 11 -----------------------------------------------------------------
    def test_11_withdrawn_then_rejoin_same_section_rejected(self) -> None:
        first = self.join(self.section1.id, self.student.id).json()
        self.assertEqual(self.withdraw(first["id"]).status_code, 200)
        resp = self.join(self.section1.id, self.student.id)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "ENROLLMENT_HISTORY_EXISTS")

    # 12 -----------------------------------------------------------------
    def test_12_completed_in_open_class_blocks_other_section(self) -> None:
        Enrollment.objects.create(
            student=self.student,
            section=self.section1,
            status=EnrollmentStatus.COMPLETED,
            grade="A",
        )
        resp = self.join(self.section2.id, self.student.id)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "OPEN_CLASS_ALREADY_FINALIZED")

    # 13 -----------------------------------------------------------------
    def test_13_failed_in_open_class_blocks_other_section(self) -> None:
        Enrollment.objects.create(
            student=self.student, section=self.section1, status=EnrollmentStatus.FAILED
        )
        resp = self.join(self.section2.id, self.student.id)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "OPEN_CLASS_ALREADY_FINALIZED")

    # 14 -----------------------------------------------------------------
    def test_14_same_subject_different_open_class_allowed(self) -> None:
        Enrollment.objects.create(
            student=self.student,
            section=self.section1,
            status=EnrollmentStatus.COMPLETED,
            grade="A",
        )
        resp = self.join(self.section_sem2.id, self.student.id)
        self.assertEqual(resp.status_code, 200)

    # 15 -----------------------------------------------------------------
    def test_15_join_payload_with_status_rejected(self) -> None:
        resp = self.client.post(
            f"/api/sections/{self.section1.id}/join",
            data=json.dumps({"student_id": str(self.student.id), "status": "Completed"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 422)

    # 16 -----------------------------------------------------------------
    def test_16_join_payload_with_grade_rejected(self) -> None:
        resp = self.client.post(
            f"/api/sections/{self.section1.id}/join",
            data=json.dumps({"student_id": str(self.student.id), "grade": "A"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 422)

    # 17 -----------------------------------------------------------------
    def test_17_withdraw_enrolled_succeeds(self) -> None:
        enrollment = self.join(self.section1.id, self.student.id).json()
        resp = self.withdraw(enrollment["id"])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "Withdrawn")

    # 18 -----------------------------------------------------------------
    def test_18_withdraw_already_withdrawn_rejected(self) -> None:
        enrollment = self.join(self.section1.id, self.student.id).json()
        self.assertEqual(self.withdraw(enrollment["id"]).status_code, 200)
        resp = self.withdraw(enrollment["id"])
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "INVALID_WITHDRAW_TRANSITION")

    # 19 -----------------------------------------------------------------
    def test_19_withdraw_completed_rejected(self) -> None:
        enrollment = Enrollment.objects.create(
            student=self.student,
            section=self.section1,
            status=EnrollmentStatus.COMPLETED,
            grade="A",
        )
        resp = self.withdraw(enrollment.id)
        self.assertEqual(resp.status_code, 409)

    # 20 -----------------------------------------------------------------
    def test_20_withdraw_failed_rejected(self) -> None:
        enrollment = Enrollment.objects.create(
            student=self.student, section=self.section1, status=EnrollmentStatus.FAILED
        )
        resp = self.withdraw(enrollment.id)
        self.assertEqual(resp.status_code, 409)

    # 21-23 ----------------------------------------------------------------
    def test_21_generic_post_enrollments_unavailable(self) -> None:
        resp = self.client.post(
            "/api/enrollments/",
            data=json.dumps({"student_id": str(self.student.id)}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 405)

    def test_22_generic_put_enrollment_unavailable(self) -> None:
        resp = self.client.put(
            f"/api/enrollments/{uuid.uuid4()}",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 405)

    def test_23_generic_delete_enrollment_unavailable(self) -> None:
        resp = self.client.delete(f"/api/enrollments/{uuid.uuid4()}")
        self.assertEqual(resp.status_code, 405)

    # 24 -------------------------------------------------------------------
    def test_24_capacity_race_is_rejected_deterministically(self) -> None:
        """Not a real concurrency proof (see plan's Concurrency limitation note):
        SQLite's select_for_update() is a no-op and TestCase wraps each test in
        a transaction, so a threaded race would pass for the wrong reason.
        This proves the capacity check is enforced in-transaction instead.
        """
        section = Section.objects.create(open_class=self.open_class, section_no="race", capacity=1)
        self.assertEqual(self.join(section.id, self.student.id).status_code, 200)
        resp = self.join(section.id, self.other_student.id)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "SECTION_FULL")

    # 25 -------------------------------------------------------------------
    def test_25_db_constraint_rejects_second_active_row_bypassing_service(self) -> None:
        Enrollment.objects.create(
            student=self.student, section=self.section1, status=EnrollmentStatus.ENROLLED
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Enrollment.objects.create(
                student=self.student, section=self.section2, status=EnrollmentStatus.ENROLLED
            )

    # 26 -------------------------------------------------------------------
    def test_26_reduce_capacity_below_enrolled_rejected(self) -> None:
        self.assertEqual(self.join(self.section1.id, self.student.id).status_code, 200)
        resp = self.client.put(
            f"/api/sections/{self.section1.id}",
            data=json.dumps(
                {"open_class_id": str(self.open_class.id), "section_no": "1", "capacity": 0}
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "CAPACITY_BELOW_ENROLLED")

    # Additional guard proofs beyond the §32 matrix (§24, §25, §27) --------

    def test_delete_student_with_history_is_protected(self) -> None:
        self.join(self.section1.id, self.student.id)
        resp = self.client.delete(f"/api/students/{self.student.id}")
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "HAS_ENROLLMENT_HISTORY")
        self.assertTrue(Student.objects.filter(id=self.student.id).exists())

    def test_section_open_class_immutable_once_history_exists(self) -> None:
        self.join(self.section1.id, self.student.id)
        resp = self.client.put(
            f"/api/sections/{self.section1.id}",
            data=json.dumps(
                {
                    "open_class_id": str(self.open_class_sem2.id),
                    "section_no": "1",
                    "capacity": 2,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "SECTION_OPEN_CLASS_IMMUTABLE")

    def test_open_class_fields_immutable_once_history_exists(self) -> None:
        self.join(self.section1.id, self.student.id)
        resp = self.client.put(
            f"/api/open-classes/{self.open_class.id}",
            data=json.dumps(
                {
                    "subject_id": str(self.unlinked_subject.id),
                    "academic_year": 2026,
                    "semester": 1,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "OPEN_CLASS_IMMUTABLE")

    def test_student_curriculum_locked_while_active_enrollment(self) -> None:
        self.join(self.section1.id, self.student.id)
        other_curriculum = Curriculum.objects.create(
            department=self.department, name="Other Curriculum", year=2026
        )
        resp = self.client.put(
            f"/api/students/{self.student.id}",
            data=json.dumps(
                {
                    "curriculum_id": str(other_curriculum.id),
                    "student_code": self.student.student_code,
                    "name": self.student.name,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["code"], "STUDENT_CURRICULUM_LOCKED")
