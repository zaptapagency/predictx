#!/usr/bin/env python3
"""Run Alembic migrations for ForecastX backend."""

import subprocess
import os
import sys

os.chdir('/app')

try:
    print("🚀 Running Alembic migrations...")
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
        cwd='/app',
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

    if result.returncode == 0:
        print("✅ Migrations completed successfully!")
    else:
        print(f"❌ Migrations failed with code {result.returncode}")

    sys.exit(result.returncode)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
