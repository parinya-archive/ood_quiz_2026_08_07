# OOD Enrollment Frontend

Next.js BFF and enrollment workspace for the OOD university API.

## Setup

Install [Bun](https://bun.sh), then run:

```bash
bun install
export OOD_API_BASE_URL=http://localhost:8000/api
bun run dev
```

`OOD_API_BASE_URL` is read only by the server-side BFF. It defaults to `http://localhost:8000/api`. Start the Django API there (or set the variable to its API root); it must expose students, curriculum subjects, subjects, open classes, sections, enrollments, and `POST /sections/:id/join`.

## Routes

- `/enroll` — enrollment workspace.
- `GET /api/enrollment-workspace` — BFF workspace projection; accepts `studentId`, `academicYear`, and `semester`.
- `POST /api/enrollment-workspace` — BFF enrollment command; accepts `studentId` and `sectionId`.

The Django API remains authoritative for eligibility, capacity, and enrollment history.

## Scripts

```bash
bun run dev
bun test
bun run lint
bun run build
```
