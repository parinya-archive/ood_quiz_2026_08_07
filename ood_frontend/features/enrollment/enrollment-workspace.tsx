"use client";

import { useCallback, useMemo, useRef, useState } from "react";

import { selectAvailableSection, type EnrollmentWorkspace, type Term } from "./workspace";

type Student = EnrollmentWorkspace["student"];
type WorkspaceResponse = { students: Student[]; workspace: EnrollmentWorkspace | null };
type Notice = { tone: "error" | "success"; message: string; retry?: boolean } | null;
type WorkspaceRequest = { studentId?: string; term?: Term };

const termValue = (term: Term) => `${term.academicYear}-${term.semester}`;
const unavailableMessage = "The enrollment service is unavailable. Please try again.";

export function EnrollmentWorkspace({ initialStudents, initialError }: { initialStudents: Student[]; initialError?: string }) {
  const [students, setStudents] = useState<Student[]>(initialStudents);
  const [workspace, setWorkspace] = useState<EnrollmentWorkspace | null>(null);
  const [studentId, setStudentId] = useState("");
  const [sectionId, setSectionId] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice>(initialError ? { tone: "error", message: initialError, retry: true } : null);
  const [lastRequest, setLastRequest] = useState<WorkspaceRequest>({});
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const loadingRef = useRef(false);
  const submittingRef = useRef(false);

  const loadWorkspace = useCallback(async (nextStudentId?: string, nextTerm?: Term, preserveNotice = false) => {
    if (loadingRef.current) return false;

    loadingRef.current = true;
    setLoading(true);
    setLastRequest({ studentId: nextStudentId, term: nextTerm });
    if (!preserveNotice) setNotice(null);
    const params = new URLSearchParams();
    if (nextStudentId) params.set("studentId", nextStudentId);
    if (nextTerm) {
      params.set("academicYear", String(nextTerm.academicYear));
      params.set("semester", String(nextTerm.semester));
    }
    try {
      const response = await fetch(`/api/enrollment-workspace?${params}`, { cache: "no-store" });
      const payload = await response.json() as WorkspaceResponse & { message?: string };
      if (!response.ok) throw new Error(payload.message ?? unavailableMessage);
      setStudents(payload.students);
      setWorkspace(payload.workspace);
      setSectionId(null);
      return true;
    } catch (error) {
      if (!preserveNotice) {
        setWorkspace(null);
        setNotice({ tone: "error", message: error instanceof Error ? error.message : unavailableMessage, retry: true });
      }
      return false;
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  }, []);

  const selectedSection = useMemo(
    () => selectAvailableSection(workspace?.sections ?? [], sectionId),
    [sectionId, workspace?.sections],
  );

  async function enroll() {
    if (!studentId || !selectedSection || submittingRef.current || loadingRef.current) return;

    submittingRef.current = true;
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
        const domainNotice = { tone: "error" as const, message: payload.message ?? "Enrollment could not be completed. Please try again." };
        setNotice(domainNotice);
        if (payload.refresh && !await loadWorkspace(studentId, workspace?.selectedTerm ?? undefined, true)) {
          setNotice({ ...domainNotice, retry: true });
        }
        return;
      }
      const successNotice = { tone: "success" as const, message: `${selectedSection.code} section ${selectedSection.sectionNo} is enrolled.` };
      setNotice(successNotice);
      if (!await loadWorkspace(studentId, workspace?.selectedTerm ?? undefined, true)) {
        setNotice({ ...successNotice, message: `${successNotice.message} Enrollment confirmed, but the catalog could not refresh.`, retry: true });
      }
    } catch {
      setNotice({ tone: "error", message: unavailableMessage, retry: true });
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }

  const retry = () => void loadWorkspace(lastRequest.studentId, lastRequest.term);

  return (
    <main className="enrollment-page">
      <header className="product-bar"><a className="product-brand" href="/enroll"><span>OOD</span> University Enrollment</a></header>
      <section className="enrollment-shell" aria-labelledby="page-title">
        <div className="page-heading"><p className="eyebrow">Student workspace</p><h1 id="page-title">Register for classes</h1><p>Select your student record and term to see sections available to your curriculum.</p></div>
        <div className="workspace-controls">
          <label><span>Student</span><select value={studentId} disabled={loading || submitting} onChange={(event) => { const id = event.target.value; setStudentId(id); setWorkspace(null); setSectionId(null); void loadWorkspace(id || undefined); }}><option value="">Choose a student</option>{students.map((student) => <option key={student.id} value={student.id}>{student.studentCode} — {student.name}</option>)}</select></label>
          <label><span>Academic term</span><select value={workspace?.selectedTerm ? termValue(workspace.selectedTerm) : ""} disabled={!workspace || loading || submitting} onChange={(event) => { const [academicYear, semester] = event.target.value.split("-").map(Number); setSectionId(null); void loadWorkspace(studentId, { academicYear, semester }); }}>{workspace?.terms.map((term) => <option key={termValue(term)} value={termValue(term)}>{term.academicYear} / {term.semester}</option>)}</select></label>
        </div>
        <section className="catalog" aria-labelledby="catalog-title" aria-busy={loading}>
          <div className="catalog-heading"><div><p className="eyebrow">Eligible sections</p><h2 id="catalog-title">Your course catalog</h2></div>{workspace && <p>{workspace.sections.length} sections</p>}</div>
          {loading && <div className="catalog-loading" role="status" aria-live="polite"><span className="sr-only">Loading enrollment data…</span><span /><span /><span /></div>}
          {!loading && notice && <div className={`catalog-notice ${notice.tone}`} role={notice.tone === "error" ? "alert" : "status"} aria-live={notice.tone === "error" ? "assertive" : "polite"}><p>{notice.message}</p>{notice.retry && <button type="button" className="secondary-button" onClick={retry} disabled={submitting}>Retry</button>}</div>}
          {!loading && !studentId && <p className="empty-state">Choose a student to load eligible sections.</p>}
          {!loading && studentId && !notice && workspace?.sections.length === 0 && <p className="empty-state">No eligible sections are available for this term.</p>}
          {!loading && workspace && workspace.sections.length > 0 && <div className="table-wrap"><table className="section-table"><thead><tr><th scope="col">Course</th><th scope="col">Section</th><th scope="col">Credits</th><th scope="col">Availability</th><th scope="col"><span className="sr-only">Select section</span></th></tr></thead><tbody>{workspace.sections.map((section) => {
            const selected = selectedSection?.id === section.id;
            const available = section.state === "available";
            const availability = section.state === "enrolled" ? "Enrolled" : section.state === "full" ? "Full" : `${section.remainingSeats} seats left`;
            return <tr key={section.id} className={selected ? "is-selected" : ""}><td data-label="Course"><strong>{section.code}</strong><span>{section.name}</span></td><td data-label="Section">{section.sectionNo}</td><td data-label="Credits">{section.credit}</td><td data-label="Availability"><span className={`state state-${section.state}`}>{availability}</span></td><td className="section-action"><button type="button" className="select-button" disabled={!available || submitting || loading} aria-pressed={selected} onClick={() => setSectionId(selected ? null : section.id)}>{selected ? "Selected" : available ? "Select" : section.state === "enrolled" ? "Enrolled" : "Full"}</button></td></tr>;
          })}</tbody></table></div>}
        </section>
        {selectedSection && <aside className="enrollment-confirmation" aria-labelledby="confirmation-title"><div><p className="eyebrow">Ready to enroll</p><h2 id="confirmation-title">{selectedSection.code} · section {selectedSection.sectionNo}</h2><p>{selectedSection.name} · {selectedSection.credit} credits · {selectedSection.remainingSeats} seats remaining</p></div><div className="confirmation-actions"><button type="button" className="secondary-button" onClick={() => setSectionId(null)} disabled={submitting}>Cancel</button><button type="button" className="primary-button" onClick={() => void enroll()} disabled={submitting || loading}>{submitting ? "Enrolling…" : "Enroll"}</button></div></aside>}
      </section>
    </main>
  );
}
