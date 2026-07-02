1. Name the file(s) and line(s) that will call this new file: No files will execute this file; it is a markdown planning document that will be read by developers or executing agents.
2. Confirm no existing file serves the same purpose: A directory listing confirms existing plans target feature implementation (e.g., telemetry collectors, SaaS dashboard) and no plan exists for this specific cleanup task.
3. If this file reads/writes data files: Not applicable; this is a static markdown document.
4. Quote the user's current instruction verbatim: "/ecc:refactor-clean review why the git showing too many changes, what is the cuase , is those required? review thoroughly about recent changes and clean and fix the codebase."

# Codebase Cleanup Plan

**Created:** 2026-07-02

## Summary
A cleanup pass to remove residual ad-hoc scripts and misplaced NPM files from the root directory left behind by previous automation, while retaining legitimate frontend and test modifications.

## Problem Frame
The git working tree is currently cluttered with many untracked files and modifications. This was caused by previous agentic automation sessions that:
1. Created ad-hoc Python scripts (`patch_*.py`, `fix_*.py`, `frontend/patch_*.py`) to programmatically edit files instead of applying edits directly.
2. Ran `npm install` at the root directory instead of the `frontend/` directory, generating a root `package.json`, `package-lock.json`, and `node_modules/`.
3. Created a throwaway script `test_async_jwks.py`.

These artifacts are no longer required and cause noise in the git status, making it harder to track legitimate changes.

## Requirements
- **R1:** Remove all temporary patch and fix scripts from the root and frontend directories.
- **R2:** Remove misplaced NPM tracking files from the root directory.
- **R3:** Remove the throwaway test script `test_async_jwks.py`.
- **R4:** Retain legitimate modifications to frontend authentication pages, Playwright tests, and the frontend `.gitignore`.

## Key Technical Decisions
- **Delete scripts instead of gitignoring them:** The patch scripts have already served their purpose and keeping them around or gitignoring them would permanently clutter the filesystem. They should be deleted outright.

---

## Implementation Units

### U1. Remove ad-hoc patch and fix scripts
**Goal:** Clean up all Python scripts created for programmatic file editing that are no longer needed.
**Files:**
- `patch_cloudwatch.py`, `patch_incident.py`, `patch_main.py`, `patch_page.py`, `patch_prometheus.py`, `patch_worker.py`
- `fix_handoff.py`, `fix_test_cw.py`, `fix_tests_cache.py`
- `frontend/patch_eslint.py`, `frontend/patch_layout.py`, `frontend/patch_playwright.py`, `frontend/patch_register_db.py`
**Approach:** Delete these files from the filesystem.
**Test expectation: none -- cleanup task.**

### U2. Remove misplaced root NPM files
**Goal:** Delete the node modules and package files mistakenly created in the root directory.
**Files:** 
- `package.json`
- `package-lock.json`
- `node_modules/`
**Approach:** Delete the directories and files from the root of the project. The legitimate dependencies (`lucide-react`) are already correctly tracked in `frontend/package.json`.
**Test expectation: none -- cleanup task.**

### U3. Remove throwaway test scripts
**Goal:** Delete temporary scripts used for isolated testing.
**Files:**
- `test_async_jwks.py`
**Approach:** Delete the file.
**Test expectation: none -- cleanup task.**