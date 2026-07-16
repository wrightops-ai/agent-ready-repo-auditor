#!/usr/bin/env python3
"""Prepare a bounded GitHub issue comment for one Fix Plan request."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_ready_repo_auditor.fix_plan_triage import main  # noqa: E402


raise SystemExit(main())
