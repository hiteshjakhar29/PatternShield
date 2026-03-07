# PatternShield Repository Instructions

You are the Claude Code agent operating in this repository.

You have full repository working permission.

## You may
- Read any file in the repository
- Traverse all folders recursively
- Inspect the full project structure
- Modify any existing file
- Create new files and folders
- Refactor across multiple files
- Rename or move files when needed
- Delete obsolete files when they are clearly replaced
- Update imports, references, configs, scripts, docs, assets, and tests
- Work across frontend, backend, extension code, tooling, and documentation

You are not restricted to a single file or a small subset of files.
Treat this repository as a full-project engineering task.

## Default workflow
For any significant task, always:
1. Inspect the relevant files first
2. Understand current architecture and runtime flow
3. Summarize the current state briefly
4. Propose a concise implementation plan
5. Make the code changes
6. Update all affected files
7. Check for consistency, broken imports, and stale references
8. Summarize what changed and any follow-up work

## Project mission
This repository contains PatternShield, a browser extension plus backend system for detecting dark patterns on websites.

Your goal is to improve the project across:
- functionality
- architecture
- maintainability
- appearance / UI polish
- UX clarity
- detection sophistication
- explainability
- performance
- robustness
- documentation
- portfolio quality
- demo readiness

## Priority order
Prioritize improvements in this order unless the current task suggests otherwise:
1. architecture cleanup
2. UI / UX modernization
3. explainable detection outputs
4. trust score and reporting improvements
5. detector modularity and taxonomy cleanup
6. temporal detection and history cleanup
7. settings, controls, and usability
8. feedback / data / analytics scaffolding
9. documentation and demo polish
10. tests and developer experience

## File change policy
You may:
- edit old files
- create new files
- create new folders
- split large files into modules
- reorganize code when beneficial
- add utilities, services, components, scripts, docs, and tests

When deleting or replacing files:
- update all references
- keep the project coherent
- avoid leaving dead imports or orphaned modules

## Coding expectations
Write code that is:
- modular
- explicit
- readable
- maintainable
- cohesive
- production-style

Prefer:
- clear naming
- centralized config/constants
- small focused modules
- minimal magic numbers
- concise useful comments where needed
- consistent patterns across the repo

Avoid:
- random hacks
- superficial edits
- inconsistent naming
- partially completed refactors
- large risky changes without checking related files

## Documentation expectations
You may update README.md and docs freely.

Documentation should clearly explain:
- what PatternShield does
- repository structure
- architecture
- setup and run instructions
- major features
- how detection works
- important design decisions
- future roadmap where useful

## Final instruction
Assume broad permission to improve the repository end-to-end.
You can inspect all files, modify any existing files, and create any new files needed.
