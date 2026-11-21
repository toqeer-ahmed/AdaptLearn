"""Architecture layer isolation tests for AdaptLearn.

Requirements Traceability:
- NFR-05: Engine Isolation — The adaptive learning engine (app/engine/) must remain
         pure Python dataclasses and functions, independent of web and database frameworks.
- NFR-15: Architecture — Backend organized into separate layers with separated responsibilities;
         business logic strictly separated from request handling and persistence.
- AGENTS.md Rule 2: Respect Architecture & Layer Boundaries.
- Decision D1 (docs/decisions.md): Pure computational engine imports zero FastAPI,
         SQLAlchemy, or Pydantic packages.
"""
import ast
from pathlib import Path

import pytest

# Disallowed external frameworks and outer application layers for app/engine/
PROHIBITED_IMPORT_PREFIXES = frozenset({
    # Web & API frameworks
    "fastapi",
    "starlette",
    "uvicorn",
    # Database, ORM & persistence
    "sqlalchemy",
    "alembic",
    "psycopg2",
    "asyncpg",
    "sqlite3",
    # Validation & schema frameworks
    "pydantic",
    "pydantic_settings",
    # HTTP client & networking libraries
    "httpx",
    "requests",
    "aiohttp",
    "urllib.request",
    "http.client",
    # Outer application architecture layers
    "app.api",
    "app.services",
    "app.repositories",
    "app.domain",
})

# Path to the adaptive learning engine package
ENGINE_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "engine"


def extract_ast_imports(source_code: str, filename: str = "<unknown>") -> list[tuple[str, int]]:
    """Parse Python source code and return a list of (module_name, line_number) tuples.

    Uses the standard library AST parser to inspect actual executable grammar nodes,
    preventing brittle string-matching false positives from comments or docstrings.
    """
    tree = ast.parse(source_code, filename=filename)
    imports: list[tuple[str, int]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.module, node.lineno))
            elif node.level > 0:
                # Relative import without module name (e.g. from . import foo)
                imports.append(("." * node.level, node.lineno))

    return imports


def find_engine_python_files() -> list[Path]:
    """Discover all Python source files in the adaptive learning engine directory."""
    if not ENGINE_DIR.exists():
        return []
    return sorted(ENGINE_DIR.glob("*.py"))


class TestEngineArchitectureIsolation:
    """Validate that app/engine/ conforms strictly to NFR-05 and Decision D1."""

    def test_engine_directory_exists_and_contains_modules(self):
        """The app/engine directory must exist and contain at least one module."""
        assert ENGINE_DIR.exists(), f"Engine directory not found at: {ENGINE_DIR}"
        py_files = find_engine_python_files()
        assert len(py_files) >= 2, (
            f"Expected at least 2 Python files in app/engine, found {len(py_files)}: "
            f"{[f.name for f in py_files]}"
        )

    @pytest.mark.parametrize(
        "engine_file",
        find_engine_python_files(),
        ids=lambda f: f.name,
    )
    def test_engine_files_have_zero_prohibited_imports(self, engine_file: Path):
        """Every Python file in app/engine must not import forbidden packages or outer layers."""
        source = engine_file.read_text(encoding="utf-8")
        imports = extract_ast_imports(source, filename=engine_file.name)

        violations = []
        for mod_name, lineno in imports:
            for prohibited in PROHIBITED_IMPORT_PREFIXES:
                if mod_name == prohibited or mod_name.startswith(f"{prohibited}."):
                    violations.append(
                        f"Line {lineno}: prohibited import '{mod_name}' (violates rule '{prohibited}')"
                    )

        assert not violations, (
            f"Architectural isolation violation(s) in {engine_file.name} (NFR-05, Decision D1):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    @pytest.mark.parametrize(
        "engine_file",
        find_engine_python_files(),
        ids=lambda f: f.name,
    )
    def test_engine_files_do_not_escape_via_relative_imports(self, engine_file: Path):
        """Relative imports in app/engine must not navigate outside the engine package."""
        source = engine_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=engine_file.name)

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level > 1:
                # level 1 is same directory (.foo); level >= 2 navigates to parent (..foo)
                violations.append(
                    f"Line {node.lineno}: relative import level {node.level} attempts to escape app/engine/"
                )

        assert not violations, (
            f"Relative import escape violation(s) in {engine_file.name}:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestArchitectureScannerReliability:
    """Validate that the AST import scanner is robust, sensitive, and immune to false positives."""

    def test_scanner_flags_prohibited_framework_imports(self):
        """AST scanner accurately detects forbidden web and database frameworks."""
        mock_source = (
            "from fastapi import APIRouter\n"
            "from sqlalchemy.orm import Session\n"
            "import pydantic\n"
            "import httpx\n"
        )
        imports = extract_ast_imports(mock_source, filename="mock.py")
        mod_names = [name for name, _ in imports]

        assert "fastapi" in mod_names
        assert "sqlalchemy.orm" in mod_names
        assert "pydantic" in mod_names
        assert "httpx" in mod_names

    def test_scanner_ignores_mentions_in_comments_and_docstrings(self):
        """AST scanner does NOT flag prohibited package names in comments or docstrings."""
        clean_mock_source = (
            '"""This engine module does NOT use FastAPI, SQLAlchemy, or Pydantic.\n'
            'It conforms strictly to NFR-05.\n'
            '"""\n'
            '# Note: do not import fastapi or requests here\n'
            'from dataclasses import dataclass\n'
            'from typing import Optional\n'
        )
        imports = extract_ast_imports(clean_mock_source, filename="clean_mock.py")
        mod_names = [name for name, _ in imports]

        # Only valid Python imports should be captured
        assert mod_names == ["dataclasses", "typing"]
        assert "fastapi" not in mod_names
        assert "sqlalchemy" not in mod_names
        assert "pydantic" not in mod_names
