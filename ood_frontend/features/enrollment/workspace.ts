export type Term = { academicYear: number; semester: number };

type Student = {
  id: string;
  curriculum: string;
  student_code: string;
  name: string;
};

export type WorkspaceData = {
  students: Student[];
  curriculumSubjects: { curriculum: string; subject: string }[];
  subjects: { id: string; code: string; name: string; credit: number }[];
  openClasses: { id: string; subject: string; academic_year: number; semester: number }[];
  sections: { id: string; open_class: string; section_no: string; capacity: number | null }[];
  enrollments: { student: string; section: string; status: string }[];
};

export type SectionRow = {
  id: string;
  code: string;
  name: string;
  credit: number;
  sectionNo: string;
  capacity: number | null;
  remainingSeats: number;
  state: "available" | "full" | "enrolled";
};

export type EnrollmentWorkspace = {
  student: { id: string; studentCode: string; name: string };
  terms: Term[];
  selectedTerm: Term | null;
  sections: SectionRow[];
};

const sameTerm = (left: Term, right: Term) =>
  left.academicYear === right.academicYear && left.semester === right.semester;

export function buildWorkspace(
  data: WorkspaceData,
  studentId: string,
  requestedTerm?: Term,
): EnrollmentWorkspace {
  const student = data.students.find((item) => item.id === studentId);
  if (!student) throw new Error("Student not found");

  const eligibleSubjectIds = new Set(
    data.curriculumSubjects
      .filter((item) => item.curriculum === student.curriculum)
      .map((item) => item.subject),
  );
  const subjectById = new Map(data.subjects.map((item) => [item.id, item]));
  const eligibleClasses = data.openClasses.filter((item) => eligibleSubjectIds.has(item.subject));
  const terms = [...new Map(eligibleClasses.map((item) => [
    `${item.academic_year}-${item.semester}`,
    { academicYear: item.academic_year, semester: item.semester },
  ])).values()].sort(
    (left, right) => right.academicYear - left.academicYear || right.semester - left.semester,
  );
  const selectedTerm = requestedTerm && terms.some((term) => sameTerm(term, requestedTerm))
    ? requestedTerm
    : terms[0] ?? null;
  const classById = new Map(eligibleClasses.map((item) => [item.id, item]));
  const enrolledCountBySection = new Map<string, number>();
  const studentEnrollments = new Set<string>();

  for (const enrollment of data.enrollments) {
    if (enrollment.status !== "Enrolled") continue;
    enrolledCountBySection.set(
      enrollment.section,
      (enrolledCountBySection.get(enrollment.section) ?? 0) + 1,
    );
    if (enrollment.student === studentId) studentEnrollments.add(enrollment.section);
  }

  const sections = selectedTerm
    ? data.sections
      .filter((section) => {
        const openClass = classById.get(section.open_class);
        return openClass
          && openClass.academic_year === selectedTerm.academicYear
          && openClass.semester === selectedTerm.semester;
      })
      .flatMap((section) => {
        const openClass = classById.get(section.open_class)!;
        const subject = subjectById.get(openClass.subject);
        if (!subject) return [];
        const enrolledCount = enrolledCountBySection.get(section.id) ?? 0;
        const remainingSeats = section.capacity === null ? 0 : Math.max(section.capacity - enrolledCount, 0);
        const state = studentEnrollments.has(section.id)
          ? "enrolled"
          : remainingSeats > 0
            ? "available"
            : "full";
        return [{
          id: section.id,
          code: subject.code,
          name: subject.name,
          credit: subject.credit,
          sectionNo: section.section_no,
          capacity: section.capacity,
          remainingSeats,
          state,
        } satisfies SectionRow];
      })
      .sort((left, right) => left.code.localeCompare(right.code) || left.sectionNo.localeCompare(right.sectionNo))
    : [];

  return {
    student: { id: student.id, studentCode: student.student_code, name: student.name },
    terms,
    selectedTerm,
    sections,
  };
}

export function messageForEnrollmentError(code: string) {
  const messages: Record<string, { message: string; refresh: boolean }> = {
    SECTION_FULL: { message: "This section is full. Choose another section.", refresh: true },
    ALREADY_ENROLLED: { message: "You are already enrolled in this section.", refresh: true },
    ALREADY_ENROLLED_IN_OPEN_CLASS: { message: "You are already enrolled in another section of this class.", refresh: true },
    OPEN_CLASS_ALREADY_FINALIZED: { message: "This class has already been finalized.", refresh: true },
    ENROLLMENT_HISTORY_EXISTS: { message: "This section cannot be joined again after withdrawal.", refresh: true },
    SUBJECT_NOT_IN_CURRICULUM: { message: "This subject is not in your curriculum.", refresh: true },
    SECTION_CAPACITY_NOT_CONFIGURED: { message: "This section is not open for enrollment yet.", refresh: true },
    SECTION_NOT_FOUND: { message: "This section no longer exists.", refresh: true },
    STUDENT_NOT_FOUND: { message: "This student record no longer exists.", refresh: true },
  };

  return messages[code] ?? { message: "Enrollment could not be completed. Please try again.", refresh: false };
}

export function selectAvailableSection(sections: SectionRow[], sectionId: string | null) {
  return sections.find((section) => section.id === sectionId && section.state === "available") ?? null;
}
