"""
my_agent/deployment/deploy.py – Deploy StreamSync Live to Vertex AI Agent Engine.

Usage:
    python deploy.py [--project PROJECT_ID] [--location LOCATION]

Prerequisites:
    gcloud auth application-default login
    pip install -r my_agent/requirements.txt
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def run(cmd: list[str]) -> None:
    """Run a shell command and exit on failure."""
    print("▶", " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy StreamSync Live agent to Vertex AI")
    parser.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT", ""))
    parser.add_argument("--location", default=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"))
    parser.add_argument(
        "--skip-terraform",
        action="store_true",
        help="Skip Terraform provisioning and only deploy the agent container",
    )
    args = parser.parse_args()

    if not args.project:
        print("ERROR: set --project or GOOGLE_CLOUD_PROJECT env var")
        sys.exit(1)

    if not args.skip_terraform:
        print("\n── Terraform init & apply ──────────────────────────────────────")
        tf_dir = os.path.join(os.path.dirname(__file__), "terraform")
        run(["terraform", "-chdir", tf_dir, "init"])
        run([
            "terraform", "-chdir", tf_dir, "apply", "-auto-approve",
            f"-var=project_id={args.project}",
            f"-var=location={args.location}",
        ])

    print("\n── Deploy ADK agent ────────────────────────────────────────────")
    run([
        "adk", "deploy", "agent_engine",
        "--project", args.project,
        "--location", args.location,
        "--staging_bucket", f"gs://{args.project}-streamsync-staging",
        "--display_name", "StreamSync Live",
        os.path.join(os.path.dirname(__file__), ".."),
    ])

    print("\n✅  Deployment complete.")


if __name__ == "__main__":
    main()
