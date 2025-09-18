# Badminton Club Session Allocation - Requirements

## 1. Project Overview
- Goal: help a club organiser collect monthly availability and grade information for all players, generate suggested session allocations, and make manual tweaks in a simple interface.
- Scope (Phase 1): single admin user enters data, runs allocation, and publishes the schedule; players do not interact directly.
- Success Criteria: organiser can complete each monthly cycle (template review -> availability entry -> allocation -> manual adjustments -> publish/export) without using spreadsheets.

## 2. Stakeholders & Personas
- Club organiser (primary user): manages player records, collects availability, reviews suggested schedule, marks payments, communicates final assignments.
- Players (indirect): their preferences and availability drive allocations; future-facing self-service features considered later.
- Coaches / committee (secondary): consume reports of attendance, payments, and demand trends.

## 3. Functional Requirements

### 3.1 Player Management
- Maintain player profiles with name, contact info (optional), grade (A/B/C/etc.).
- Store preference flags: weekday vs weekend, early vs late, optional notes (free text).
- Track payment status per month: checkbox plus timestamp/amount.
- Support quick filtering by grade, preference, and payment status.

### 3.2 Session Templates & Monthly Sessions
- Define recurring `SessionTemplate` records (weekday, start/end time, grade, capacity, location/label).
- At month creation, materialise `MonthlySession` instances from templates for each calendar date in that month.
- Allow organiser to adjust generated sessions (skip holidays, change capacity).

### 3.3 Availability Capture
- For each month, organiser selects a player and records availability via a calendar date picker.
- Calendar highlights valid session slots for the player's grade; organiser can mark available/unavailable per slot.
- Quick-fill controls (e.g., "All Tuesdays", "Weekday early only").
- Persist availability as `Availability` records referencing player + specific `MonthlySession`.

### 3.4 Allocation Engine
- Generate suggested assignments considering:
  - Grade compatibility (hard constraint).
  - Player availability (hard constraint).
  - Preferences (weekday/weekend, early/late) as weighted soft constraints.
  - Balancing total sessions per player to avoid over/under allocation.
- Penalise deviations from preferences; only assign against preference when no feasible alternative exists.
- Produce output summarising assignment confidence and reasons for deviations or unfilled demand.
- Allow organiser to adjust preference weight and rerun the algorithm; retain previous results for comparison.

### 3.5 Manual Adjustments & Review
- Display allocation results in a calendar or grid grouped by grade/session slot.
- Enable drag-and-drop reassignment, swap actions, and quick reassign modal.
- Warn when manual move violates constraints; organiser can override with confirmation.
- Record audit entries for each manual change (who, when, from -> to, reason/notes).
- Mark sessions as "confirmed" once satisfied; indicator for overfull or empty slots.

### 3.6 Publishing & Reporting
- Generate per-player schedule summaries for the month (plus payment status).
- Export options (CSV/PDF/email template) for sharing schedules.
- Reports:
  - Session fill rates and waitlists.
  - Players over/under allocated.
  - Payment completion list.

## 4. Data Model (Conceptual)
- `Player`: id, name, grade, preferences (weekday/weekend, early/late), notes.
- `SessionTemplate`: id, weekday, time range, grade, capacity, venue.
- `MonthlySession`: id, date, time range, grade, capacity, template_id.
- `Availability`: id, player_id, monthly_session_id, status (available/unavailable), preference_strength (optional).
- `Allocation`: id, monthly_session_id, player_id, source (`auto`/`manual`), confidence score, created_at.
- `OverrideLog`: id, allocation_id, user, action (reassign/swap/remove), timestamp, notes.
- `PaymentStatus`: id, player_id, month, paid (bool), paid_at, amount.
- `AllocationRun`: id, month, parameters (preference weight, balancing rules), executed_at, outcome summary.

## 5. User Experience Requirements
- Responsive UI prioritising desktop; mobile-friendly forms for quick edits.
- Single-page workflow with tabs/steps: Players -> Sessions -> Availability -> Allocation -> Review.
- Availability picker with monthly calendar and slot chips; clear legends for grade slots.
- Allocation screen with colour-coding for:
  - Preference matches/mismatches.
  - Payment status badges.
  - Waitlisted players.
- Undo/redo for manual changes; confirmation prompts before destructive overrides.
- Accessible components (keyboard navigable drag-and-drop alternative, ARIA labels).

## 6. Non-Functional Requirements
- Deployment-ready on common hosting (VM or container):
  - Stateless application tier.
  - External/Postgres database with backups.
- Persistence:
  - Prefer managed Postgres; if containerised, configure persistent volumes and automated snapshots.
  - Automated migrations (Flyway, Liquibase, Prisma migrate).
- Security:
  - Authentication (admin login) even in phase 1.
  - Protect API endpoints; rate-limit if exposed publicly.
  - Secure secret management via environment variables or secret manager.
- Observability:
  - Health check endpoint.
  - Structured logs with correlation IDs for allocation runs.
  - Basic metrics (allocation duration, session fill %).
- Performance:
  - Support at least ~200 players and 40 sessions per month without noticeable lag.
  - Allocation recompute completes within a few seconds.

## 7. Integration & Extensibility
- Future: player self-service portal, email notifications (SendGrid/Mailgun), payment integration.
- API-first design to support external tools or future mobile app.
- Hooks for exporting data to spreadsheets or BI tools.

## 8. Constraints & Assumptions
- Single admin user in MVP; multi-user roles later.
- Grades are fixed categories per season (A/B/C); changes require admin update.
- All sessions are grade-exclusive; no mixed-grade slots in phase 1.
- Internet connectivity assumed during use (no offline mode).

## 9. Open Questions
- How many grades and session templates typically exist per month?
- Do some players require guaranteed minimum session counts (e.g., coaches)?
- Preferred format for sharing final schedule (email template, printout)?
- Any need to track court availability or resources beyond player slots?
- Should payment tracking integrate with existing accounting tools?
