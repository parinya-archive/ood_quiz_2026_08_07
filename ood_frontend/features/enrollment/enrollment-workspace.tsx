"use client";

import { useCallback, useMemo, useState } from "react";

import { selectAvailableSection, type EnrollmentWorkspace, type Term } from "./workspace";

type Student = { id: string; studentCode: string; name: string };
type WorkspaceResponse = { students: Student[]; workspace: EnrollmentWorkspace | null };
type Notice = { tone: "error" | "success"; message: string } | null;

const termValue = (term: Term) => `${term.academicYear}-${term.semester}`;

export function EnrollmentWorkspace({ initialStudents, initialError }: { initialStudents: Student[]; initialError?: string }) {
  const [students, setStudents] = useState<Student[]>(initialStudents);
  const [workspace, setWorkspace] = useState<EnrollmentWorkspace | null>(null);
  const [studentId, setStudentId] = useState("");
  const [sectionId, setSectionId] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice>(initialError ? { tone: "error", message: initialError } : null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const loadWorkspace = useCallback(async (nextStudentId?: string, nextTerm?: Term) => {
    setLoading(true);
    setNotice(null);
    const params = new URLSearchParams();
    if (nextStudentId) params.set("studentId", nextStudentId);
    if (nextTerm) {
      params.set("academicYear", String(nextTerm.academicYear));
      params.set("semester", String(nextTerm.semester));
    }
    try {
      const response = await fetch(`/api/enrollment-workspace?${params}`, { cache: "no-store" });
      const payload = await response.json() as WorkspaceResponse & { message?: string };
      if (!response.ok) throw new Error(payload.message ?? "The enrollment service is unavailable. Please try again.");
      setStudents(payload.students);
      setWorkspace(payload.workspace);
      setSectionId(null);
    } catch (error) {
      setWorkspace(null);
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "The enrollment service is unavailable. Please try again." });
    } finally {
      setLoading(false);
    }
  }, []);

  const selectedSection = useMemo(
    () => selectAvailableSection(workspace?.sections ?? [], sectionId),
    [sectionId, workspace?.sections],
  );

  async function enroll() {
    if (!studentId || !selectedSection) return;
    setSubmitting(true);
    setNotice(null);
    try {
      const response = await fetch("/api/enrollment-workspace", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ studentId, sectionId: selectedSection.id }),
      });
      const payload = await response.json() as { message?: string; refresh?: boolean };
      if (!response.ok) {
        setNotice({ tone: "error", message: payload.message ?? "Enrollment could not be completed. Please try again." });
        if (payload.refresh) await loadWorkspace(studentId, workspace?.selectedTerm ?? undefined);
        return;
      }
      setNotice({ tone: "success", message: `${selectedSection.code} section ${selectedSection.sectionNo} is enrolled.` });
      await loadWorkspace(studentId, workspace?.selectedTerm ?? undefined);
    } catch {
      setNotice({ tone: "error", message: "The enrollment service is unavailable. Please try again." });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="enrollment-page">
      <header className="product-bar"><a className="product-brand" href="/enroll"><span>OOD</span> University Enrollment</a></header>
      <section className="enrollment-shell" aria-labelledby="page-title">
        <div className="page-heading"><p className="eyebrow">Student workspace</p><h1 id="page-title">Register for classes</h1><p>Select your student record and term to see sections available to your curriculum.</p></div>
        <div className="workspace-controls">
          <label><span>Student</span><select value={studentId} disabled={loading && students.length === 0} onChange={(event) => { const id = event.target.value; setStudentId(id); setWorkspace(null); void loadWorkspace(id || undefined); }}><option value="">Choose a student</option>{students.map((student) => <option key={student.id} value={student.id}>{student.studentCode} — {student.name}</option>)}</select></label>
          <label><span>Academic term</span><select value={workspace?.selectedTerm ? termValue(workspace.selectedTerm) : ""} disabled={!workspace || loading} onChange={(event) => { const [academicYear, semester] = event.target.value.split("-").map(Number); void loadWorkspace(studentId, { academicYear, semester }); }}>{workspace?.terms.map((term) => <option key={termValue(term)} value={termValue(term)}>{term.academicYear} / {term.semester}</option>)}</select></label>
        </div>
        <p className={`status-message ${notice?.tone ?? ""}`} aria-live="polite">{loading ? "Loading enrollment data…" : notice?.message}</p>
        <section className="catalog" aria-labelledby="catalog-title" aria-busy={loading}>
          <div className="catalog-heading"><div><p className="eyebrow">Eligible sections</p><h2 id="catalog-title">Your course catalog</h2></div>{workspace && <p>{workspace.sections.length} sections</p>}</div>
          {!studentId && <p className="empty-state">Choose a student to load eligible sections.</p>}
          {studentId && !loading && workspace?.sections.length === 0 && <p className="empty-state">No eligible sections are available for this term.</p>}
          {workspace && workspace.sections.length > 0 && <div className="table-wrap"><table className="section-table"><thead><tr><th scope="col">Course</th><th scope="col">Section</th><th scope="col">Credits</th><th scope="col">Availability</th><th scope="col"><span className="sr-only">Select section</span></th></tr></thead><tbody>{workspace.sections.map((section) => {
            const selected = selectedSection?.id === section.id;
            const available = section.state === "available";
            const availability = section.state === "enrolled" ? "Enrolled" : section.state === "full" ? "Full" : `${section.remainingSeats} seats left`;
            return <tr key={section.id} className={selected ? "is-selected" : ""}><td data-label="Course"><strong>{section.code}</strong><span>{section.name}</span></td><td data-label="Section">{section.sectionNo}</td><td data-label="Credits">{section.credit}</td><td data-label="Availability"><span className={`state state-${section.state}`}>{availability}</span></td><td className="section-action"><button type="button" className="select-button" disabled={!available || submitting} aria-pressed={selected} onClick={() => setSectionId(selected ? null : section.id)}>{selected ? "Selected" : available ? "Select" : section.state === "enrolled" ? "Enrolled" : "Full"}</button></td></tr>;
          })}</tbody></table></div>}
        </section>
        {selectedSection && <aside className="enrollment-confirmation" aria-labelledby="confirmation-title"><div><p className="eyebrow">Ready to enroll</p><h2 id="confirmation-title">{selectedSection.code} · section {selectedSection.sectionNo}</h2><p>{selectedSection.name} · {selectedSection.credit} credits · {selectedSection.remainingSeats} seats remaining</p></div><div className="confirmation-actions"><button type="button" className="secondary-button" onClick={() => setSectionId(null)} disabled={submitting}>Cancel</button><button type="button" className="primary-button" onClick={() => void enroll()} disabled={submitting}>{submitting ? "Enrolling…" : "Enroll"}</button></div></aside>}
      </section>
    </main>
  );
}
