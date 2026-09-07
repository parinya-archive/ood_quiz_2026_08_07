import type { WorkspaceData } from "./workspace";

export class EnrollmentApiError extends Error {
  constructor(
    public status: number,
    public code?: string,
    detail?: string,
  ) {
    super(detail ?? "The enrollment service could not complete the request.");
  }
}

const endpoint = (baseUrl: string, path: string) => `${baseUrl.replace(/\/$/, "")}${path}`;

async function requestJson<T>(
  fetcher: typeof fetch,
  baseUrl: string,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetcher(endpoint(baseUrl, path), { cache: "no-store", ...init });
  const payload = await response.json().catch(() => null) as { code?: string; detail?: string } | T | null;

  if (!response.ok) {
    const error = payload as { code?: string; detail?: string } | null;
    throw new EnrollmentApiError(response.status, error?.code, error?.detail);
  }

  return payload as T;
}

export async function loadEnrollmentData(
  fetcher: typeof fetch = fetch,
  baseUrl = process.env.OOD_API_BASE_URL ?? "http://localhost:8000/api",
): Promise<WorkspaceData> {
  const [students, curriculumSubjects, subjects, openClasses, sections, enrollments] = await Promise.all([
    requestJson<WorkspaceData["students"]>(fetcher, baseUrl, "/students/"),
    requestJson<WorkspaceData["curriculumSubjects"]>(fetcher, baseUrl, "/curriculum-subjects/"),
    requestJson<WorkspaceData["subjects"]>(fetcher, baseUrl, "/subjects/"),
    requestJson<WorkspaceData["openClasses"]>(fetcher, baseUrl, "/open-classes/"),
    requestJson<WorkspaceData["sections"]>(fetcher, baseUrl, "/sections/"),
    requestJson<WorkspaceData["enrollments"]>(fetcher, baseUrl, "/enrollments/"),
  ]);

  return { students, curriculumSubjects, subjects, openClasses, sections, enrollments };
}

export function submitEnrollment(
  fetcher: typeof fetch = fetch,
  baseUrl = process.env.OOD_API_BASE_URL ?? "http://localhost:8000/api",
  studentId: string,
  sectionId: string,
) {
  return requestJson(
    fetcher,
    baseUrl,
    `/sections/${sectionId}/join`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: studentId }),
    },
  );
}
