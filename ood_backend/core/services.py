"""Business transactions for Enrollment: join a section, withdraw, and the
mutation guards protecting Section/OpenClass/Student once history exists.

Enrollment is not generic CRUD. See the Strict Enrollment / Join Class Policy
in the approved plan. Check order in ``join_class`` is pinned to that policy's
step order and must not be reordered without updating the tests that assert
it (e.g. an ineligible-and-full section must fail eligibility, not capacity).
"""

import logging
from typing import Any, ClassVar

from django.db import transaction

from core.models import (
    CurriculumSubject,
    Enrollment,
    EnrollmentStatus,
    OpenClass,
    Section,
    Student,
)

logger = logging.getLogger("core")


class DomainError(Exception):
    """Base for business-rule rejections; maps to a stable JSON error contract."""

    code: ClassVar[str] = "DOMAIN_ERROR"
    detail: ClassVar[str] = "Request violates a business rule."
    status: ClassVar[int] = 409


class StudentNotFound(DomainError):
    code = "STUDENT_NOT_FOUND"
    detail = "Student does not exist."
    status = 404


class SectionNotFound(DomainError):
    code = "SECTION_NOT_FOUND"
    detail = "Section does not exist."
    status = 404


class EnrollmentNotFound(DomainError):
    code = "ENROLLMENT_NOT_FOUND"
    detail = "Enrollment does not exist."
    status = 404


class SubjectNotInCurriculum(DomainError):
    code = "SUBJECT_NOT_IN_CURRICULUM"
    detail = "This subject is not part of the student's curriculum."
    status = 422


class AlreadyEnrolled(DomainError):
    code = "ALREADY_ENROLLED"
    detail = "Student is already enrolled in this section."


class AlreadyEnrolledInOpenClass(DomainError):
    code = "ALREADY_ENROLLED_IN_OPEN_CLASS"
    detail = "Student is already enrolled in another section of this class."


class OpenClassAlreadyFinalized(DomainError):
    code = "OPEN_CLASS_ALREADY_FINALIZED"
    detail = "Student already has a finalized enrollment for this class."


class EnrollmentHistoryExists(DomainError):
    code = "ENROLLMENT_HISTORY_EXISTS"
    detail = "An enrollment record for this student and section already exists."


class CapacityNotConfigured(DomainError):
    code = "SECTION_CAPACITY_NOT_CONFIGURED"
    detail = "Section capacity has not been configured."


class SectionFull(DomainError):
    code = "SECTION_FULL"
    detail = "Section has reached its enrollment capacity."


class InvalidWithdrawTransition(DomainError):
    code = "INVALID_WITHDRAW_TRANSITION"
    detail = "Only an Enrolled enrollment can be withdrawn."


class SectionOpenClassImmutable(DomainError):
    code = "SECTION_OPEN_CLASS_IMMUTABLE"
    detail = "Section's open_class cannot change once it has enrollment history."


class CapacityBelowEnrolled(DomainError):
    code = "CAPACITY_BELOW_ENROLLED"
    detail = "Capacity cannot be reduced below the current enrolled count."


class OpenClassImmutable(DomainError):
    code = "OPEN_CLASS_IMMUTABLE"
    detail = "subject/academic_year/semester cannot change once enrollment history exists."


class StudentCurriculumLocked(DomainError):
    code = "STUDENT_CURRICULUM_LOCKED"
    detail = "Curriculum cannot change while the student has an active enrollment."


@transaction.atomic
def join_class(*, student_id: Any, section_id: Any) -> Enrollment:
    """Enroll a student in a section, enforcing the full eligibility policy.

    Lock order is always Student then Section (fixed to avoid deadlocks).
    select_for_update() is a no-op on SQLite but keeps this portable.
    """
    try:
        student = (
            Student.objects.select_for_update().select_related("curriculum").get(id=student_id)
        )
    except Student.DoesNotExist as exc:
        raise StudentNotFound from exc

    try:
        section = (
            Section.objects.select_for_update()
            .select_related("open_class__subject")
            .get(id=section_id)
        )
    except Section.DoesNotExist as exc:
        raise SectionNotFound from exc

    open_class = section.open_class
    subject = open_class.subject

    eligible = CurriculumSubject.objects.filter(
        curriculum=student.curriculum, subject=subject
    ).exists()
    if not eligible:
        raise SubjectNotInCurriculum

    same_section = Enrollment.objects.filter(student=student, section=section).first()
    if same_section is not None:
        if same_section.status == EnrollmentStatus.ENROLLED:
            raise AlreadyEnrolled
        if same_section.status == EnrollmentStatus.WITHDRAWN:
            raise EnrollmentHistoryExists
        raise OpenClassAlreadyFinalized

    sibling = (
        Enrollment.objects.filter(student=student, open_class=open_class)
        .exclude(status=EnrollmentStatus.WITHDRAWN)
        .first()
    )
    if sibling is not None:
        if sibling.status == EnrollmentStatus.ENROLLED:
            raise AlreadyEnrolledInOpenClass
        raise OpenClassAlreadyFinalized

    if section.capacity is None or section.capacity <= 0:
        raise CapacityNotConfigured

    enrolled_count = Enrollment.objects.filter(
        section=section, status=EnrollmentStatus.ENROLLED
    ).count()
    if enrolled_count >= section.capacity:
        raise SectionFull

    logger.debug("join: student=%s section=%s", student_id, section_id)
    return Enrollment.objects.create(
        student=student, section=section, status=EnrollmentStatus.ENROLLED, grade=None
    )


@transaction.atomic
def withdraw_enrollment(*, enrollment_id: Any) -> Enrollment:
    """Transition Enrolled -> Withdrawn. Any other current status is rejected."""
    try:
        enrollment = Enrollment.objects.select_for_update().get(id=enrollment_id)
    except Enrollment.DoesNotExist as exc:
        raise EnrollmentNotFound from exc

    if enrollment.status != EnrollmentStatus.ENROLLED:
        raise InvalidWithdrawTransition

    enrollment.status = EnrollmentStatus.WITHDRAWN
    enrollment.save()
    logger.debug("withdraw: enrollment=%s", enrollment_id)
    return enrollment


def guard_section_update(obj: Section, new: dict[str, Any]) -> None:
    """Reject open_class changes and under-capacity shrinks once history exists."""
    has_history = Enrollment.objects.filter(section=obj).exists()
    if not has_history:
        return
    if "open_class" in new and new["open_class"] != obj.open_class_id:
        raise SectionOpenClassImmutable
    if "capacity" in new:
        enrolled_count = Enrollment.objects.filter(
            section=obj, status=EnrollmentStatus.ENROLLED
        ).count()
        new_capacity = new["capacity"]
        if new_capacity is None or new_capacity < enrolled_count:
            raise CapacityBelowEnrolled


def guard_open_class_update(obj: OpenClass, new: dict[str, Any]) -> None:
    """Reject subject/academic_year/semester changes once history exists."""
    has_history = Enrollment.objects.filter(open_class=obj).exists()
    if not has_history:
        return
    immutable_fields = ("subject", "academic_year", "semester")
    for field in immutable_fields:
        if field in new and new[field] != getattr(obj, f"{field}_id", getattr(obj, field)):
            raise OpenClassImmutable


def guard_student_update(obj: Student, new: dict[str, Any]) -> None:
    """Reject curriculum changes while the student has an active enrollment."""
    has_active = Enrollment.objects.filter(student=obj, status=EnrollmentStatus.ENROLLED).exists()
    if not has_active:
        return
    if "curriculum" in new and new["curriculum"] != obj.curriculum_id:
        raise StudentCurriculumLocked
