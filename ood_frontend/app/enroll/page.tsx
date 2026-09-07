import { EnrollmentWorkspace } from "@/features/enrollment/enrollment-workspace";
import { loadEnrollmentData } from "@/features/enrollment/django";

export const dynamic = "force-dynamic";

async function initialProps() {
  try {
    const { students } = await loadEnrollmentData();
    return { initialStudents: students.map(({ id, student_code: studentCode, name }) => ({ id, studentCode, name })) };
  } catch {
    return { initialStudents: [], initialError: "The enrollment service is unavailable. Please try again." };
  }
}

export default async function EnrollPage() {
  return <EnrollmentWorkspace {...await initialProps()} />;
}
