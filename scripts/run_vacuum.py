#!/usr/bin/env python3
"""
Standalone vacuum runner for cron or manual execution.
Usage:
    python scripts/run_vacuum.py              # triggers via HTTP + polls
    python scripts/run_vacuum.py --direct     # runs vacuum logic directly (no server needed)
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

API_BASE = "http://localhost:8000"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_via_http():
    import urllib.request

    req = urllib.request.Request(f"{API_BASE}/admin/vacuum", method="POST", data=b"")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            job_id = result["job_id"]
            logger.info("Vacuum job created: %s", job_id)
    except Exception as e:
        logger.error("Failed to trigger vacuum: %s", e)
        sys.exit(1)

    while True:
        time.sleep(5)
        try:
            with urllib.request.urlopen(f"{API_BASE}/admin/vacuum/status/{job_id}", timeout=10) as resp:
                status = json.loads(resp.read())
                logger.info("[%s] progress=%s%% stage=%s", status['status'], status['progress'], status.get('current_stage', '-'))
                if status["status"] in ("completed", "failed"):
                    logger.info("Final stats: %s", json.dumps(status.get('stats', {}), indent=2))
                    if status["status"] == "failed":
                        logger.error("Error: %s", status.get('error_log', 'unknown'))
                        sys.exit(1)
                    break
        except Exception as e:
            logger.error("Poll error: %s", e)


def run_direct():
    from agents.RAG.vacuum import create_vacuum_job, run_vacuum_job, get_vacuum_job_status

    job_id = create_vacuum_job()
    logger.info("Vacuum job created: %s", job_id)
    run_vacuum_job(job_id)
    status = get_vacuum_job_status(job_id)
    logger.info("Status: %s", status['status'])
    logger.info("Stats: %s", json.dumps(status.get('stats', {}), indent=2))
    if status["status"] == "failed":
        logger.error("Error: %s", status.get('error_log', 'unknown'))
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Tars vacuum cleanup")
    parser.add_argument("--direct", action="store_true", help="Run directly without HTTP server")
    parser.add_argument("--api-base", default=API_BASE, help="API base URL (default: http://localhost:8000)")
    args = parser.parse_args()

    if args.api_base:
        API_BASE = args.api_base

    if args.direct:
        run_direct()
    else:
        run_via_http()
