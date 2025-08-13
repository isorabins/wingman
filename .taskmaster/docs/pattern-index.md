# WingmanMatch Pattern Index (Reference-First)

Golden rule: reference_files/ is READ-ONLY. Reuse patterns; create new code in our app. Do not modify or import directly from reference_files at runtime.

## Core References (read-only)
- Frontend stack: reference_files/frontend_reference/FAF_website/memory-bank/techContext.md
- Frontend dev commands: reference_files/frontend_reference/FAF_website/CLAUDE.md
- Frontend components/themes: reference_files/frontend_reference/FAF_website/app/** (chat/, creativity-test/page.tsx, theme.ts)
- Backend style/env: reference_files/src/main.py, reference_files/src/config.py
- AI utils: reference_files/src/content_summarizer.py, reference_files/src/simple_memory.py
- Agents: reference_files/src/agents/creativity_agent.py, project_overview_agent.py
- Database schema/policies: reference_files/docs/dev-documentation/04-database-guide.md
- Migrations style: reference_files/supabase/migrations/20250129120912_remote_schema.sql
- E2E test structure: reference_files/new_tests/real_world_tests/test_db_driven_full_journey.py, run_all_tests.py
- Deployment docs: reference_files/docs/dev-documentation/07-deployment.md, reference_files/docs/deployment_workflow_docs.md

## Task-to-Reference Map (wingman-match)
- 1 Env baselines: CLAUDE.md, techContext.md, src/main.py, src/config.py
- 2 DB migrations: db guide, migrations/20250129120912_remote_schema.sql
- 3 Backend config: src/main.py, src/config.py
- 4 Coach prompts: src/prompts.py, src/claude_agent.py
- 5 Assessment agent/flow: agents/creativity_agent.py, content_summarizer.py
- 6 Assessment UI: frontend/app/creativity-test/page.tsx, theme.ts
- 7 Profile setup UI/API: frontend/app (forms), src/main.py patterns
- 8 Distance utils: db guide for naming; src/main.py for query style
- 9 Matcher service: agents/agent_manager.py pattern; src/main.py client
- 10 Match respond: src/main.py route style
- 11 Chat: frontend/app/chat; src/main.py endpoints style
- 12 Challenges API: src/main.py route + Redis cache style
- 13 Session create API: src/main.py + Resend import style
- 14 Active session page: Next App Router patterns; theme.ts
- 15 Completion+reputation: src/main.py route style
- 16 Reputation read/UI: src/main.py; Chakra Badge pattern
- 17 Homepage copy: reuse Chakra/Tailwind components
- 18 Dating goals API: agents/project_overview_agent.py, src/main.py
- 19 Emails: src/main.py resend usage
- 20 Safety/reporting: src/main.py route style; db guide (RLS)
- 21 Location privacy: frontend/app forms; Task 8 Haversine
- 22 Perf/cost: content_summarizer.py, simple_memory.py, src/main.py cache
- 23 User journey tests: reference real_world_tests layout
- 24 Deployment/monitoring: deployment docs + src/main.py patterns
- 25 Beta ops: frontend_reference README/CLAUDE for analytics conventions
- 26 Supabase provisioning: db guide + migrations style
- 27 Vercel provisioning: techContext + deployment docs

## New-Code Targets (examples)
- DB: supabase/migrations_wm/*.sql, scripts/db/*.sql
- Backend: src/api/*.py, src/services/*.py, src/assessment/*.py
- Frontend: app/** (new pages/components), lib/** helpers
- Tests: tests/backend/**, tests/e2e/**

## Guardrails
- Do not modify reference_files/**
- TDD-first: implement pure functions and tests before wiring endpoints
- Acceptance gates per task must pass before merge
- Keep changes minimal; reference index must be updated when tasks evolve

## Acceptance Checklist (per PR)
- [ ] No diffs under reference_files/** (CI guard)
- [ ] Unit/integration/E2E tests per task pass
- [ ] Tasks.json remains valid JSON and updated if task scope changed
- [ ] Pattern Index updated if new references or targets were used

## Notes
- Prefer copying minimal patterns over porting whole files
- Document any intentional deviations from reference patterns here 