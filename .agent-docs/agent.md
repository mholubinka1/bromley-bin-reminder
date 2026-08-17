# Agent Behavioural Standards

These standards apply to all AI agent work in this repository. Follow them on every task.

---

## 1. Ownership and Independence

- Take ownership of a task from start to finish with minimal handholding. Clarify ambiguity, scope the work, implement it, verify it locally, and confirm it works in the target environment.
- Know when to ask for help. Try for a reasonable period, but do not stall in silence. When you ask, include what you tried, what you expected, and what happened.
- Recognise when a task is larger than initially scoped and surface this early. Do not produce oversized changes — break work into smaller increments.
- Deliver consistently against the stated scope. Make your effort estimates broadly reliable.

---

## 2. Production Code Quality

- Write readable code above all else. Write self-documenting code. Use comments only to explain complex functionality — not to restate what the code does.
- Favour clarity over brevity. Prefer maintainability over micro-efficiency.
- Give every function and class a single, clear responsibility. Keep methods short enough that their behaviour is understood without extensive scrolling.
- Name everything descriptively. Choose names for variables, methods, classes, and files that communicate intent without requiring the reader to open another file.
- Never hardcode values, magic numbers, secrets, credentials, URLs, or environment-specific strings. Use secret-safe configuration.
- Never leave commented-out code, dead code, or deprecated code in committed changes. Replace unnecessary TODOs with proper work items — do not leave them in the codebase.
- Never leave debug output (`console.log`, `print`, `System.out.println`, etc.) in committed code.
- Handle errors deliberately. Understand the possible failure states, handle them explicitly, and test for them. Never swallow errors or re-throw them blindly.
- Catch common pitfalls before raising any PR: N+1 queries, unbounded loops, leaked secrets, unsanitised input.
- Use logging levels (`info`, `debug`, `warning`, `error`) appropriately. Write log messages that are meaningful.
- Follow the existing patterns and conventions of the codebase. Introduce new patterns slowly, with good reason and explicit agreement.
- Treat performance, security, and observability as part of every task — not afterthoughts.

---

## 3. Testing Discipline

- Accompany any change to execution logic with tests. If code can be changed without tests failing, the current test coverage is insufficient.
- Write unit tests that cover happy paths and meaningful edge cases: empty inputs, boundary conditions, error paths, and all execution branches introduced by your change.
- Write tests that verify behaviour, not implementation. Do not test internal structure — tests that verify implementation details have no value.
- Write deterministic tests. Do not rely on real network calls, real clocks, or shared mutable state. Mock only at system boundaries — never mock code you control.
- Ensure all tests pass locally before raising any PR. Do not raise a PR with a failing pipeline.
- Add integration and/or contract tests where a change is integration-heavy.
- Maintain a minimum of 80% code coverage, enforced at the pipeline level. Prioritise meaningful coverage of business logic over hitting the number with implementation tests.

---

## 4. Source Control and Git Practice

- Always branch from the latest `main` or `develop`. Name branches consistently: `feature/`, `bugfix/`, `hotfix/`, `chore/`. Confirm conventions when joining a new codebase.
- Make commits small, logical, and with meaningful descriptive messages. Do not use loose messages (`fix`, `wip`, `update`) on reviewed branches.
- Rebase or merge with the latest target branch before raising a PR. Resolve conflicts yourself — do not leave them for the reviewer.
- Avoid long-lived feature branches. Break work down for incremental merging. Hide new UI behind feature flags rather than leaving it unmerged.
- Keep PRs focused on one concern. Do not mix features, refactors, and unrelated fixes in a single PR.

---

## 5. Engineering Lifecycle

- Understand the full path from work item to production: refinement → estimation → implementation → review → merge → deployment → monitoring.
- Read acceptance criteria before starting. Clarify ambiguities upfront. Validate your implementation against acceptance criteria before raising a PR. Write acceptance criteria proactively when they are absent.
- Act as the first line of behaviour verification — not QA. Test changes appropriately in the execution environment before requesting review.
- Write PRs as handover artefacts. Write them for the reviewer so that the changes can be unambiguously understood.

---

## 6. Communication and Feedback

- Surface blockers and scope changes proactively and early in your response — do not wait to be asked. Alert the team immediately if a deadline or scope commitment is at risk.
- Treat review feedback as input to improve the work. Engage with it constructively.
- Disagree with feedback through productive discussion and reasoning. Do not silently revert to the same pattern on the next task.
- Contribute context and experience to team decisions. Every level has useful perspective to share.
