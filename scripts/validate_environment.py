#!/usr/bin/env python
"""
Script: validate_environment
Purpose:
    Validate the development environment setup — check Python version,
    dependencies, configuration, database connectivity, and directory structure.

Usage:
    python scripts/validate_environment.py
"""

import sys
import importlib
from pathlib import Path

# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# ---------------------------------------------------------------------------

REQUIRED_PACKAGES = [
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("sqlalchemy", "SQLAlchemy"),
    ("psycopg2", "psycopg2-binary"),
    ("openpyxl", "openpyxl"),
    ("requests", "requests"),
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("pydantic", "pydantic"),
    ("pytest", "pytest"),
    ("yaml", "PyYAML"),
    ("dotenv", "python-dotenv"),
]

REQUIRED_DIRS = [
    "data/raw",
    "data/staging",
    "data/processed",
    "data/curated",
    "data/quarantine",
    "data/archive",
    "logs",
]


def check_python_version() -> bool:
    print(f"[*] Python Version: {sys.version.split()[0]} ... ", end="")
    if sys.version_info >= (3, 10):
        print("OK (>= 3.10)")
        return True
    else:
        print("FAIL (requires Python 3.10+)")
        return False


def check_dependencies() -> bool:
    print("\n[*] Checking Core Python Dependencies:")
    all_ok = True
    for module_name, pkg_name in REQUIRED_PACKAGES:
        try:
            mod = importlib.import_module(module_name)
            ver = getattr(mod, "__version__", "installed")
            print(f"    - {pkg_name:<18} : OK ({ver})")
        except ImportError:
            print(f"    - {pkg_name:<18} : MISSING (run: pip install -r requirements.txt)")
            all_ok = False
    return all_ok


def check_env_file() -> bool:
    print("\n[*] Checking Configuration Files:")
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        print(f"    - .env file        : FOUND ({env_file.stat().st_size} bytes)")
        return True
    else:
        print("    - .env file        : NOT FOUND (copy from .env.example)")
        return False


def check_directories() -> bool:
    print("\n[*] Checking Directory Structure:")
    all_ok = True
    for rel_dir in REQUIRED_DIRS:
        d = PROJECT_ROOT / rel_dir
        if d.exists() and d.is_dir():
            print(f"    - {rel_dir:<20} : OK")
        else:
            try:
                d.mkdir(parents=True, exist_ok=True)
                print(f"    - {rel_dir:<20} : CREATED")
            except Exception as e:
                print(f"    - {rel_dir:<20} : ERROR ({e})")
                all_ok = False
    return all_ok


def check_database() -> bool:
    print("\n[*] Checking Database Connectivity:")
    try:
        from src.utils.config import get_connection_string
        from sqlalchemy import create_engine, text

        conn_str = get_connection_string()
        engine = create_engine(conn_str, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            res = conn.execute(text("SELECT version();")).scalar()
            print(f"    - PostgreSQL       : CONNECTED ({res.split(',')[0]})")
            return True
    except Exception as exc:
        print(f"    - PostgreSQL       : NOT REACHABLE ({exc})")
        print("      (Ensure PostgreSQL is running via 'docker-compose up -d' or native service)")
        return False


def main() -> None:
    print("=" * 60)
    print(" ENVIRONMENT VALIDATION")
    print("=" * 60)

    py_ok = check_python_version()
    deps_ok = check_dependencies()
    dirs_ok = check_directories()
    env_ok = check_env_file()
    db_ok = check_database()

    print("\n" + "=" * 60)
    print(" VALIDATION SUMMARY")
    print("=" * 60)
    print(f" Python Version        : {'PASS' if py_ok else 'FAIL'}")
    print(f" Python Dependencies   : {'PASS' if deps_ok else 'FAIL'}")
    print(f" Project Directories   : {'PASS' if dirs_ok else 'FAIL'}")
    print(f" Environment (.env)    : {'PASS' if env_ok else 'WARN (using defaults)'}")
    print(f" Database Connectivity : {'PASS' if db_ok else 'WARN (service not started)'}")
    print("=" * 60 + "\n")

    if not (py_ok and deps_ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
