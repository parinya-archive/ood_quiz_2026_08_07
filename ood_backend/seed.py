#!/usr/bin/env python
"""Seed the database with coherent mock data.

Idempotent: re-running does not duplicate rows (uses get_or_create on the
natural/unique keys). Pass --flush to wipe existing rows from these models
first.

Usage:
    uv run python seed.py [--flush]
"""

import argparse
import logging
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import transaction  # noqa: E402

from core.models import (  # noqa: E402
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

logger = logging.getLogger("core")

ACADEMIC_YEAR = 2026

SUBJECTS = [
    ("CPE101", "Introduction to Programming", 3),
    ("CPE201", "Data Structures and Algorithms", 3),
    ("CPE301", "Operating Systems", 3),
    ("CPE302", "Computer Networks", 3),
    ("CPE401", "Software Engineering", 3),
    ("CPE402", "Database Systems", 3),
    ("GE101", "English Communication", 3),
    ("GE102", "Critical Thinking", 3),
    ("MA101", "Calculus I", 3),
    ("MA102", "Linear Algebra", 3),
]

# (subject_code, requirement_type, semester_recommended, year_recommended)
CURRICULUM_SUBJECTS = [
    ("CPE101", SubjectRequirementType.CORE, 1, 1),
    ("CPE201", SubjectRequirementType.CORE, 2, 1),
    ("CPE301", SubjectRequirementType.MAJOR, 1, 2),
    ("CPE302", SubjectRequirementType.MAJOR, 2, 2),
    ("CPE401", SubjectRequirementType.MAJOR, 1, 3),
    ("CPE402", SubjectRequirementType.MAJOR, 2, 3),
    ("GE101", SubjectRequirementType.GEN_ED, 1, 1),
    ("GE102", SubjectRequirementType.GEN_ED, 2, 1),
    ("MA101", SubjectRequirementType.ELECTIVE, 1, 1),
    ("MA102", SubjectRequirementType.ELECTIVE, 2, 1),
]


def flush() -> None:
    logger.info("flushing existing seed data")
    Enrollment.objects.all().delete()
    Section.objects.all().delete()
    OpenClass.objects.all().delete()
    CurriculumSubject.objects.all().delete()
    Student.objects.all().delete()
    Subject.objects.all().delete()
    Curriculum.objects.all().delete()
    Department.objects.all().delete()
    Faculty.objects.all().delete()
    University.objects.all().delete()


@transaction.atomic
def seed() -> None:
    university, _ = University.objects.get_or_create(name="Kasetsart University")
    logger.info("university: %s", university.name)

    engineering, _ = Faculty.objects.get_or_create(
        university=university, name="Faculty of Engineering"
    )
    science, _ = Faculty.objects.get_or_create(university=university, name="Faculty of Science")

    cpe_dept, _ = Department.objects.get_or_create(faculty=engineering, name="Computer Engineering")
    ee_dept, _ = Department.objects.get_or_create(
        faculty=engineering, name="Electrical Engineering"
    )
    math_dept, _ = Department.objects.get_or_create(faculty=science, name="Mathematics")
    logger.info("departments: %s", [cpe_dept.name, ee_dept.name, math_dept.name])

    curriculum, _ = Curriculum.objects.get_or_create(
        department=cpe_dept,
        name="Computer Engineering Curriculum",
        year=ACADEMIC_YEAR,
    )
    curriculum_alt, _ = Curriculum.objects.get_or_create(
        department=ee_dept,
        name="Electrical Engineering Curriculum",
        year=ACADEMIC_YEAR,
    )
    logger.info("curricula: %s, %s", curriculum.name, curriculum_alt.name)

    subjects = {}
    for code, name, credit in SUBJECTS:
        subject, _ = Subject.objects.get_or_create(
            code=code, defaults={"name": name, "credit": credit, "department": cpe_dept}
        )
        subjects[code] = subject
    logger.info("subjects: %d created/found", len(subjects))

    for code, req_type, semester, year in CURRICULUM_SUBJECTS:
        CurriculumSubject.objects.get_or_create(
            curriculum=curriculum,
            subject=subjects[code],
            defaults={
                "type": req_type,
                "semester_recommended": semester,
                "year_recommended": year,
            },
        )
    logger.info("curriculum subjects linked: %d", len(CURRICULUM_SUBJECTS))

    students = []
    for i in range(1, 16):
        student, _ = Student.objects.get_or_create(
            student_code=f"651234{i:03d}",
            defaults={"name": f"Student {i}", "curriculum": curriculum},
        )
        students.append(student)
    logger.info("students: %d created/found", len(students))

    open_classes = []
    for code in ["CPE101", "CPE201", "CPE301", "GE101"]:
        for semester in (1, 2):
            open_class, _ = OpenClass.objects.get_or_create(
                subject=subjects[code],
                academic_year=ACADEMIC_YEAR,
                semester=semester,
            )
            open_classes.append(open_class)
    logger.info("open classes: %d created/found", len(open_classes))

    sections = []
    for open_class in open_classes:
        for section_no in ("1", "2"):
            section, _ = Section.objects.get_or_create(
                open_class=open_class, section_no=section_no, defaults={"capacity": 40}
            )
            sections.append(section)
    logger.info("sections: %d created/found", len(sections))

    statuses = [
        EnrollmentStatus.ENROLLED,
        EnrollmentStatus.WITHDRAWN,
        EnrollmentStatus.COMPLETED,
        EnrollmentStatus.FAILED,
    ]
    created = 0
    for i, student in enumerate(students):
        section = sections[i % len(sections)]
        status = statuses[i % len(statuses)]
        grade = "A" if status == EnrollmentStatus.COMPLETED else None
        _, was_created = Enrollment.objects.get_or_create(
            student=student,
            section=section,
            defaults={"status": status, "grade": grade},
        )
        if was_created:
            created += 1
    logger.info("enrollments created: %d", created)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the university enrollment database.")
    parser.add_argument("--flush", action="store_true", help="delete existing rows first")
    args = parser.parse_args()

    if args.flush:
        flush()

    seed()
    logger.info("seeding complete")


if __name__ == "__main__":
    main()
