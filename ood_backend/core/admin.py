from django.contrib import admin

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

admin.site.register(University)
admin.site.register(Faculty)
admin.site.register(Department)
admin.site.register(Curriculum)
admin.site.register(Subject)
admin.site.register(CurriculumSubject)
admin.site.register(Student)
admin.site.register(OpenClass)
admin.site.register(Section)
admin.site.register(Enrollment)
