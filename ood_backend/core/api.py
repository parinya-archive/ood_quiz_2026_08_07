"""Generic CRUD router factory, registered once per model.

django-ninja builds its ``ViewSignature`` *inside* ``router.post(...)`` /
``router.put(...)`` by reading ``inspect.signature()`` at that call. So the
``payload`` parameter's real schema type must be patched onto the function's
``__annotations__`` *before* it is handed to ``router.post``/``router.put`` -
using ``@router.post(...)`` decorator syntax would register the endpoint
before the patch runs, and ninja would treat ``payload`` as unannotated.
Hence the explicit (non-decorator) calls below.

Enrollment is the one resource that is *not* generic CRUD: joining a section
and withdrawing are business transactions (see core/services.py), so its
router is registered read-only and gets two explicit command endpoints
instead of POST/PUT/DELETE.
"""

import logging
import uuid
from typing import Any, Protocol

from django.db import IntegrityError, models
from django.db.models import ProtectedError
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Router, Schema

from core import services
from core.models import (
    Curriculum,
    CurriculumSubject,
    Department,
    Enrollment,
    Faculty,
    OpenClass,
    Section,
    Student,
    Subject,
    University,
)
from core.schemas import (
    CurriculumIn,
    CurriculumOut,
    CurriculumSubjectIn,
    CurriculumSubjectOut,
    DepartmentIn,
    DepartmentOut,
    EnrollmentOut,
    FacultyIn,
    FacultyOut,
    JoinIn,
    OpenClassIn,
    OpenClassOut,
    SectionIn,
    SectionOut,
    StudentIn,
    StudentOut,
    SubjectIn,
    SubjectOut,
    UniversityIn,
    UniversityOut,
)

logger = logging.getLogger("core")


class UpdateGuard(Protocol):
    def __call__(self, obj: Any, new: dict[str, Any]) -> None: ...


def _model_kwargs(model: type[models.Model], data: dict[str, Any]) -> dict[str, Any]:
    """Translate a schema's ``{field: value}`` dict into ORM kwargs.

    A ``ModelSchema`` field for a ForeignKey carries the *related object's*
    field name (e.g. ``university``) but its value is only the related pk
    (a UUID). Django's ``Model(university=<uuid>)`` requires an actual
    instance for that name, so FK values must be passed as ``university_id``
    instead.
    """
    fk_names = {f.name for f in model._meta.get_fields() if f.many_to_one or f.one_to_one}
    return {(f"{key}_id" if key in fk_names else key): value for key, value in data.items()}


def crud_router[ModelT: models.Model](
    model: type[ModelT],
    schema_in: type[Schema] | None,
    schema_out: type[Schema],
    *,
    tag: str,
    read_only: bool = False,
    update_guard: UpdateGuard | None = None,
) -> Router:
    """Build a Router with list/get(/create/update/delete) for ``model``."""
    router = Router(tags=[tag])
    name = model.__name__

    def list_items(request: HttpRequest) -> models.QuerySet[ModelT]:
        return model._default_manager.all()

    router.get(
        "/",
        response=list[schema_out],  # type: ignore[valid-type]
        summary=f"List {tag}s",
        operation_id=f"{model.__name__.lower()}_list",
    )(list_items)

    def get_item(request: HttpRequest, item_id: uuid.UUID) -> ModelT:
        return get_object_or_404(model, id=item_id)

    router.get(
        "/{item_id}",
        response=schema_out,
        summary=f"Get {tag}",
        operation_id=f"{model.__name__.lower()}_get",
    )(get_item)

    if read_only:
        return router

    assert schema_in is not None, "schema_in is required unless read_only=True"

    def create_item(request: HttpRequest, payload: Schema) -> ModelT:
        kwargs = _model_kwargs(model, payload.dict())
        logger.debug("creating %s: %s", name, kwargs)
        obj = model._default_manager.create(**kwargs)
        return obj

    create_item.__annotations__["payload"] = schema_in
    router.post(
        "/",
        response=schema_out,
        summary=f"Create {tag}",
        operation_id=f"{model.__name__.lower()}_create",
    )(create_item)

    def update_item(request: HttpRequest, item_id: uuid.UUID, payload: Schema) -> ModelT:
        obj = get_object_or_404(model, id=item_id)
        new_values = _model_kwargs(model, payload.dict())
        if update_guard is not None:
            update_guard(obj, payload.dict())
        for field, value in new_values.items():
            setattr(obj, field, value)
        obj.save()
        logger.debug("updated %s %s", name, item_id)
        return obj

    update_item.__annotations__["payload"] = schema_in
    router.put(
        "/{item_id}",
        response=schema_out,
        summary=f"Update {tag}",
        operation_id=f"{model.__name__.lower()}_update",
    )(update_item)

    def delete_item(request: HttpRequest, item_id: uuid.UUID) -> dict[str, bool]:
        obj = get_object_or_404(model, id=item_id)
        obj.delete()
        logger.debug("deleted %s %s", name, item_id)
        return {"success": True}

    router.delete(
        "/{item_id}",
        summary=f"Delete {tag}",
        operation_id=f"{model.__name__.lower()}_delete",
    )(delete_item)

    return router


api = NinjaAPI(
    title="University Enrollment API",
    version="1.0.0",
    description=(
        "Academic catalog and student enrollment management API for managing "
        "universities, curricula, courses, sections, and enrollment records."
    ),
)
api.openapi_extra = {
    "tags": [
        {"name": "University", "description": "Manage universities in the system."},
        {"name": "Faculty", "description": "Manage faculties within universities."},
        {"name": "Department", "description": "Manage departments within faculties."},
        {"name": "Curriculum", "description": "Manage academic curricula."},
        {"name": "Subject", "description": "Manage subjects and course catalog entries."},
        {
            "name": "Curriculum Subject",
            "description": "Track required or elective subject mappings within a curriculum.",
        },
        {"name": "Student", "description": "Manage student records."},
        {"name": "Open Class", "description": "Manage open-course offerings."},
        {"name": "Section", "description": "Manage course sections and capacities."},
        {
            "name": "Enrollment",
            "description": (
                "Read-only enrollment records. Use the join/withdraw commands on "
                "Section/Enrollment to change enrollment state."
            ),
        },
    ],
    "x-tagGroups": [
        {
            "name": "Academic Catalog",
            "tags": [
                "University",
                "Faculty",
                "Department",
                "Curriculum",
                "Subject",
                "Curriculum Subject",
            ],
        },
        {
            "name": "Student Lifecycle",
            "tags": ["Student", "Open Class", "Section", "Enrollment"],
        },
    ],
}


@api.exception_handler(services.DomainError)
def domain_error_handler(request: HttpRequest, exc: services.DomainError) -> Any:
    return api.create_response(request, {"code": exc.code, "detail": exc.detail}, status=exc.status)


@api.exception_handler(ProtectedError)
def protected_error_handler(request: HttpRequest, exc: ProtectedError) -> Any:
    return api.create_response(
        request,
        {
            "code": "HAS_ENROLLMENT_HISTORY",
            "detail": "Cannot delete: referenced by existing enrollment history.",
        },
        status=409,
    )


@api.exception_handler(IntegrityError)
def integrity_error_handler(request: HttpRequest, exc: IntegrityError) -> Any:
    return api.create_response(
        request, {"detail": "Conflict: violates a uniqueness constraint."}, status=409
    )


api.add_router(
    "/universities",
    crud_router(University, UniversityIn, UniversityOut, tag="University"),
)
api.add_router("/faculties", crud_router(Faculty, FacultyIn, FacultyOut, tag="Faculty"))
api.add_router(
    "/departments",
    crud_router(Department, DepartmentIn, DepartmentOut, tag="Department"),
)
api.add_router(
    "/curricula",
    crud_router(Curriculum, CurriculumIn, CurriculumOut, tag="Curriculum"),
)
api.add_router("/subjects", crud_router(Subject, SubjectIn, SubjectOut, tag="Subject"))
api.add_router(
    "/curriculum-subjects",
    crud_router(
        CurriculumSubject,
        CurriculumSubjectIn,
        CurriculumSubjectOut,
        tag="Curriculum Subject",
    ),
)
api.add_router(
    "/students",
    crud_router(
        Student, StudentIn, StudentOut, tag="Student", update_guard=services.guard_student_update
    ),
)
api.add_router(
    "/open-classes",
    crud_router(
        OpenClass,
        OpenClassIn,
        OpenClassOut,
        tag="Open Class",
        update_guard=services.guard_open_class_update,
    ),
)
sections_router = crud_router(
    Section, SectionIn, SectionOut, tag="Section", update_guard=services.guard_section_update
)


def join_section(request: HttpRequest, section_id: uuid.UUID, payload: JoinIn) -> Enrollment:
    return services.join_class(student_id=payload.student_id, section_id=section_id)


sections_router.post(
    "/{section_id}/join",
    response=EnrollmentOut,
    summary="Join a section",
    operation_id="section_join",
    tags=["Section"],
)(join_section)
api.add_router("/sections", sections_router)

enrollments_router = crud_router(Enrollment, None, EnrollmentOut, tag="Enrollment", read_only=True)


def withdraw(request: HttpRequest, enrollment_id: uuid.UUID) -> Enrollment:
    return services.withdraw_enrollment(enrollment_id=enrollment_id)


enrollments_router.post(
    "/{enrollment_id}/withdraw",
    response=EnrollmentOut,
    summary="Withdraw an enrollment",
    operation_id="enrollment_withdraw",
    tags=["Enrollment"],
)(withdraw)
api.add_router("/enrollments", enrollments_router)
