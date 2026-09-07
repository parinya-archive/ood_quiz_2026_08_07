"""ninja ModelSchema pairs (In/Out) for every model."""

import uuid

from ninja import ModelSchema, Schema

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


class UniversityIn(ModelSchema):
    class Meta:
        model = University
        fields = ["name"]


class UniversityOut(ModelSchema):
    class Meta:
        model = University
        fields = ["id", "name"]


class FacultyIn(ModelSchema):
    class Meta:
        model = Faculty
        fields = ["university", "name"]


class FacultyOut(ModelSchema):
    class Meta:
        model = Faculty
        fields = ["id", "university", "name"]


class DepartmentIn(ModelSchema):
    class Meta:
        model = Department
        fields = ["faculty", "name"]


class DepartmentOut(ModelSchema):
    class Meta:
        model = Department
        fields = ["id", "faculty", "name"]


class CurriculumIn(ModelSchema):
    class Meta:
        model = Curriculum
        fields = ["department", "name", "year"]


class CurriculumOut(ModelSchema):
    class Meta:
        model = Curriculum
        fields = ["id", "department", "name", "year"]


class SubjectIn(ModelSchema):
    class Meta:
        model = Subject
        fields = ["department", "code", "name", "credit"]


class SubjectOut(ModelSchema):
    class Meta:
        model = Subject
        fields = ["id", "department", "code", "name", "credit"]


class CurriculumSubjectIn(ModelSchema):
    type: SubjectRequirementType

    class Meta:
        model = CurriculumSubject
        fields = [
            "curriculum",
            "subject",
            "semester_recommended",
            "year_recommended",
        ]


class CurriculumSubjectOut(ModelSchema):
    type: SubjectRequirementType

    class Meta:
        model = CurriculumSubject
        fields = [
            "id",
            "curriculum",
            "subject",
            "semester_recommended",
            "year_recommended",
        ]


class StudentIn(ModelSchema):
    class Meta:
        model = Student
        fields = ["curriculum", "student_code", "name"]


class StudentOut(ModelSchema):
    class Meta:
        model = Student
        fields = ["id", "curriculum", "student_code", "name"]


class OpenClassIn(ModelSchema):
    class Meta:
        model = OpenClass
        fields = ["subject", "academic_year", "semester"]


class OpenClassOut(ModelSchema):
    class Meta:
        model = OpenClass
        fields = ["id", "subject", "academic_year", "semester"]


class SectionIn(ModelSchema):
    class Meta:
        model = Section
        fields = ["open_class", "section_no", "capacity"]


class SectionOut(ModelSchema):
    class Meta:
        model = Section
        fields = ["id", "open_class", "section_no", "capacity"]


# Enrollment has no generic write schema: joining/withdrawing are business
# transactions (core/services.py), not CRUD. See JoinIn below.


class EnrollmentOut(ModelSchema):
    status: EnrollmentStatus

    class Meta:
        model = Enrollment
        fields = ["id", "student", "section", "open_class", "grade"]


class JoinIn(Schema):
    """Body for POST /sections/{section_id}/join. section_id comes from the URL."""

    model_config = {"extra": "forbid"}

    student_id: uuid.UUID
