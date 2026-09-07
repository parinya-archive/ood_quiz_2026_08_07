"""Models for the university enrollment domain.

Mirrors the DBML schema: University -> Faculty -> Department ->
Curriculum/Subject -> CurriculumSubject, Student, OpenClass -> Section,
Enrollment.
"""

import uuid
from typing import Any

from django.db import models


class SubjectRequirementType(models.TextChoices):
    """How a subject counts toward a curriculum's requirements."""

    CORE = "Core", "Core"
    MAJOR = "Major", "Major"
    GEN_ED = "GenEd", "GenEd"
    ELECTIVE = "Elective", "Elective"


class EnrollmentStatus(models.TextChoices):
    """Lifecycle status of a student's enrollment in a section."""

    ENROLLED = "Enrolled", "Enrolled"
    WITHDRAWN = "Withdrawn", "Withdrawn"
    COMPLETED = "Completed", "Completed"
    FAILED = "Failed", "Failed"


class University(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Faculty(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    university = models.ForeignKey(University, on_delete=models.PROTECT, related_name="faculties")
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name="departments")
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class Curriculum(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="curricula")
    name = models.CharField(max_length=255)
    year = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.name} ({self.year})"


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        related_name="subjects",
        null=True,
        blank=True,
    )
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    credit = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class CurriculumSubject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    curriculum = models.ForeignKey(
        Curriculum, on_delete=models.CASCADE, related_name="curriculum_subjects"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name="curriculum_subjects"
    )
    type = models.CharField(max_length=16, choices=SubjectRequirementType.choices)
    semester_recommended = models.IntegerField(null=True, blank=True)
    year_recommended = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["curriculum", "subject"], name="unique_curriculum_subject"
            )
        ]

    def __str__(self) -> str:
        return f"{self.curriculum} - {self.subject}"


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.PROTECT, related_name="students")
    student_code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.student_code} - {self.name}"


class OpenClass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="open_classes")
    academic_year = models.IntegerField()
    semester = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.subject.code} - {self.academic_year}/{self.semester}"


class Section(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    open_class = models.ForeignKey(OpenClass, on_delete=models.PROTECT, related_name="sections")
    section_no = models.CharField(max_length=16)
    capacity = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["open_class", "section_no"], name="unique_open_class_section_no"
            )
        ]

    def __str__(self) -> str:
        return f"{self.open_class} - Sec {self.section_no}"


class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="enrollments")
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="enrollments")
    # Denormalized from section.open_class (see save()) so the same-OpenClass
    # uniqueness invariant below can be a real DB index on SQLite, which cannot
    # build a unique index across a join.
    open_class = models.ForeignKey(
        OpenClass, on_delete=models.PROTECT, related_name="enrollments", editable=False
    )
    status = models.CharField(max_length=16, choices=EnrollmentStatus.choices)
    grade = models.CharField(max_length=8, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "section"], name="unique_student_section"),
            models.UniqueConstraint(
                fields=["student", "open_class"],
                condition=~models.Q(status=EnrollmentStatus.WITHDRAWN),
                name="unique_active_student_open_class",
            ),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Derived from section; keeps unique_active_student_open_class truthful.
        # NOTE: bulk_create()/QuerySet.update() bypass save() and would skip this.
        self.open_class_id = self.section.open_class_id
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.student} - {self.section} ({self.status})"
