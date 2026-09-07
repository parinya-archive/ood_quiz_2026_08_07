import { describe, expect, test } from "bun:test";

import { EnrollmentApiError, loadEnrollmentData, submitEnrollment } from "./django";
import { buildWorkspace, messageForEnrollmentError, selectAvailableSection } from "./workspace";
import { GET, POST } from "../../app/api/enrollment-workspace/route";

const data = {
  students: [{ id: "student-1", curriculum: "curriculum-1", student_code: "65000001", name: "Ava Student" }],
  curriculumSubjects: [
    { curriculum: "curriculum-1", subject: "subject-1" },
    { curriculum: "curriculum-1", subject: "subject-2" },
    { curriculum: "curriculum-1", subject: "subject-3" },
  ],
  subjects: [
    { id: "subject-1", code: "CS101", name: "Programming", credit: 3 },
    { id: "subject-2", code: "CS102", name: "Databases", credit: 3 },
    { id: "subject-3", code: "CS103", name: "Networks", credit: 3 },
    { id: "subject-4", code: "ART101", name: "Drawing", credit: 3 },
  ],
  openClasses: [
    { id: "open-1", subject: "subject-1", academic_year: 2026, semester: 2 },
    { id: "open-2", subject: "subject-2", academic_year: 2026, semester: 2 },
    { id: "open-3", subject: "subject-3", academic_year: 2026, semester: 2 },
    { id: "open-4", subject: "subject-4", academic_year: 2026, semester: 2 },
    { id: "open-5", subject: "subject-1", academic_year: 2025, semester: 1 },
  ],
  sections: [
    { id: "section-1", open_class: "open-1", section_no: "01", capacity: 2 },
    { id: "section-2", open_class: "open-2", section_no: "01", capacity: 1 },
    { id: "section-3", open_class: "open-3", section_no: "02", capacity: 20 },
    { id: "section-4", open_class: "open-4", section_no: "01", capacity: 10 },
    { id: "section-5", open_class: "open-5", section_no: "01", capacity: 10 },
  ],
  enrollments: [
    { student: "student-2", section: "section-2", status: "Enrolled" },
    { student: "student-1", section: "section-3", status: "Enrolled" },
  ],
};

describe("buildWorkspace", () => {
  test("defaults to the newest eligible term and derives available, full, and enrolled sections", () => {
    const workspace = buildWorkspace(data, "student-1");

    expect(workspace.selectedTerm).toEqual({ academicYear: 2026, semester: 2 });
    expect(workspace.sections).toEqual([
      expect.objectContaining({ code: "CS101", remainingSeats: 2, state: "available" }),
      expect.objectContaining({ code: "CS102", remainingSeats: 0, state: "full" }),
      expect.objectContaining({ code: "CS103", remainingSeats: 19, state: "enrolled" }),
    ]);
  });

  test("uses a requested eligible term", () => {
    const workspace = buildWorkspace(data, "student-1", { academicYear: 2025, semester: 1 });

    expect(workspace.selectedTerm).toEqual({ academicYear: 2025, semester: 1 });
    expect(workspace.sections).toEqual([
      expect.objectContaining({ code: "CS101", sectionNo: "01", state: "available" }),
    ]);
  });
});

test("maps every join-domain error to a refreshable enrollment message", () => {
  const cases = [
    ["SECTION_FULL", "This section is full. Choose another section."],
    ["ALREADY_ENROLLED", "You are already enrolled in this section."],
    ["ALREADY_ENROLLED_IN_OPEN_CLASS", "You are already enrolled in another section of this class."],
    ["OPEN_CLASS_ALREADY_FINALIZED", "This class has already been finalized."],
    ["ENROLLMENT_HISTORY_EXISTS", "This section cannot be joined again after withdrawal."],
    ["SUBJECT_NOT_IN_CURRICULUM", "This subject is not in your curriculum."],
    ["SECTION_CAPACITY_NOT_CONFIGURED", "This section is not open for enrollment yet."],
    ["SECTION_NOT_FOUND", "This section no longer exists."],
    ["STUDENT_NOT_FOUND", "This student record no longer exists."],
  ] as const;

  for (const [code, message] of cases) {
    expect(messageForEnrollmentError(code)).toEqual({ message, refresh: true });
  }
});

test("uses a safe non-refreshing fallback for an unknown enrollment error", () => {
  expect(messageForEnrollmentError("UNRECOGNIZED_ERROR")).toEqual({
    message: "Enrollment could not be completed. Please try again.",
    refresh: false,
  });
});

test("clears a stale or unavailable section selection", () => {
  const workspace = buildWorkspace(data, "student-1");

  expect(selectAvailableSection(workspace.sections, "section-1")?.code).toBe("CS101");
  expect(selectAvailableSection(workspace.sections, "section-2")).toBeNull();
  expect(selectAvailableSection(workspace.sections, "section-3")).toBeNull();
});

test("loads every normalized resource required by the workspace", async () => {
  const resources: Record<string, unknown[]> = {
    "/students/": data.students,
    "/curriculum-subjects/": data.curriculumSubjects,
    "/subjects/": data.subjects,
    "/open-classes/": data.openClasses,
    "/sections/": data.sections,
    "/enrollments/": data.enrollments,
  };
  const fetcher: typeof fetch = async (input) => {
    const path = new URL(input.toString()).pathname.replace("/api", "");
    return Response.json(resources[path]);
  };

  await expect(loadEnrollmentData(fetcher, "http://ood.test/api")).resolves.toEqual(data);
});

test("preserves a domain error returned by the join command", async () => {
  const fetcher: typeof fetch = async () =>
    Response.json({ code: "SECTION_FULL", detail: "Section has reached its enrollment capacity." }, { status: 409 });

  await expect(submitEnrollment(fetcher, "http://ood.test/api", "student-1", "section-1")).rejects.toEqual(
    expect.objectContaining<EnrollmentApiError>({ code: "SECTION_FULL", status: 409 }),
  );
});

test("rejects malformed workspace query input", async () => {
  const response = await GET(new Request("http://localhost/api/enrollment-workspace?studentId=not-a-uuid"));

  expect(response.status).toBe(400);
  await expect(response.json()).resolves.toEqual({ code: "INVALID_REQUEST" });
});

test("rejects an incomplete enrollment command", async () => {
  const response = await POST(new Request("http://localhost/api/enrollment-workspace", {
    method: "POST",
    body: JSON.stringify({ studentId: "not-a-uuid" }),
  }));

  expect(response.status).toBe(400);
  await expect(response.json()).resolves.toEqual({ code: "INVALID_REQUEST" });
});
