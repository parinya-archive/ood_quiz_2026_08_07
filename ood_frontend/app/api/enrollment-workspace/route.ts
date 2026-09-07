import { EnrollmentApiError, loadEnrollmentData, submitEnrollment } from "@/features/enrollment/django";
import { buildWorkspace, messageForEnrollmentError, type Term } from "@/features/enrollment/workspace";

export const dynamic = "force-dynamic";

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const invalidRequest = () => Response.json({ code: "INVALID_REQUEST" }, { status: 400 });

function parseTerm(params: URLSearchParams): Term | undefined | null {
  const academicYear = params.get("academicYear");
  const semester = params.get("semester");
  if (academicYear === null && semester === null) return undefined;
  if (academicYear === null || semester === null) return null;

  const year = Number(academicYear);
  const term = Number(semester);
  return Number.isInteger(year) && Number.isInteger(term) && term > 0
    ? { academicYear: year, semester: term }
    : null;
}

function enrollmentErrorResponse(error: unknown) {
  if (error instanceof EnrollmentApiError) {
    if (error.code) {
      return Response.json(
        { code: error.code, ...messageForEnrollmentError(error.code) },
        { status: error.status },
      );
    }
  }
  return Response.json(
    { code: "UPSTREAM_UNAVAILABLE", message: "The enrollment service is unavailable. Please try again." },
    { status: 502 },
  );
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const studentId = searchParams.get("studentId");
  const requestedTerm = parseTerm(searchParams);
  if ((studentId !== null && !uuidPattern.test(studentId)) || requestedTerm === null) return invalidRequest();

  try {
    const data = await loadEnrollmentData();
    const students = data.students.map(({ id, student_code: studentCode, name }) => ({ id, studentCode, name }));
    if (studentId === null) return Response.json({ students, workspace: null });

    return Response.json({ students, workspace: buildWorkspace(data, studentId, requestedTerm) });
  } catch (error) {
    if (error instanceof Error && error.message === "Student not found") {
      return Response.json({ code: "STUDENT_NOT_FOUND" }, { status: 404 });
    }
    return enrollmentErrorResponse(error);
  }
}

export async function POST(request: Request) {
  const body: unknown = await request.json().catch(() => null);
  if (
    !body
    || typeof body !== "object"
    || !("studentId" in body)
    || !("sectionId" in body)
    || typeof body.studentId !== "string"
    || typeof body.sectionId !== "string"
    || !uuidPattern.test(body.studentId)
    || !uuidPattern.test(body.sectionId)
  ) return invalidRequest();

  try {
    const enrollment = await submitEnrollment(fetch, undefined, body.studentId, body.sectionId);
    return Response.json({ enrollment });
  } catch (error) {
    return enrollmentErrorResponse(error);
  }
}
