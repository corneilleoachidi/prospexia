# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state

`prospexia` is a freshly initialized repository (single "projet init" commit). It contains only an empty `README.md` — there is no source code, dependency manifest, build system, linter, or test suite yet. Everything below should be filled in as the project takes shape; do not assume tooling exists until it is added.

- Location under `~/PythonApps/` suggests a Python project, but no `pyproject.toml`, `requirements.txt`, or virtual environment exists yet.
- Git: default branch is `main`; the working tree was clean at init.

## When adding the first code

Update this file with:

1. **Commands** — how to install dependencies, run the app, lint/format, run the full test suite, and run a single test.
2. **Architecture** — the high-level structure (entry points, main modules, data flow) once there is more than one file to understand.
