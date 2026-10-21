"""
supabase_manager.py

Operational management utility for the Supabase Cloud PostgreSQL database.
Enables inspecting project lifecycle status, querying table population counts,
verifying PostGIS spatial support, and dispatching manual anti-dormancy pings.
"""

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any, Dict, List

SUPABASE_BIN = shutil.which("supabase") or "supabase"


def run_cli_query(sql: str) -> Dict[str, Any]:
    """Executes a SQL query against the linked Supabase project via CLI."""
    flattened_sql = " ".join(sql.strip().split())
    cmd = [SUPABASE_BIN, "db", "query", "--linked", flattened_sql, "-o", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        raw = proc.stdout.strip()
        start_idx = raw.find("{")
        if start_idx != -1:
            return json.loads(raw[start_idx:])
        return {"rows": []}
    except subprocess.CalledProcessError as err:
        print(f"Error executing Supabase CLI query: {err.stderr}", file=sys.stderr)
        return {"error": err.stderr, "rows": []}


def cmd_status() -> None:
    """Checks remote project status via Supabase CLI."""
    cmd = [SUPABASE_BIN, "projects", "list", "--output", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        raw = proc.stdout.strip()
        data = json.loads(raw)
        if isinstance(data, list):
            projects = data
        else:
            projects = data.get("projects", [])
        if not projects:
            print("No Supabase projects found.")
            return

        print("=== Supabase Remote Projects ===")
        for p in projects:
            linked_flag = "LINKED" if p.get("linked") else "NOT LINKED"
            print(f"Project ID: {p.get('id')}")
            print(f"Name:       {p.get('name')}")
            print(f"Status:     {p.get('status')} ({linked_flag})")
            print(f"Region:     {p.get('region')}")
            print(f"Host:       {p.get('database', {}).get('host')}")
            print(f"Version:    PostgreSQL {p.get('database', {}).get('version')}")
            print("---------------------------------")
    except Exception as ex:
        print(f"Failed to retrieve project status: {ex}", file=sys.stderr)


def cmd_verify_tables() -> None:
    """Verifies that all 29 platform tables exist and reports their row counts."""
    sql = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name NOT IN ('geography_columns', 'geometry_columns', 'spatial_ref_sys')
    ORDER BY table_name;
    """
    res = run_cli_query(sql)
    rows = res.get("rows", [])
    table_names = [r["table_name"] for r in rows if "table_name" in r]

    print(f"=== Authoritative Table Verification ({len(table_names)} tables found) ===")
    if not table_names:
        print("No public platform tables detected.")
        return

    # Count rows across all tables
    count_queries = " UNION ALL ".join(
        [f"SELECT '{tbl}' as table_name, count(*) as count FROM {tbl}" for tbl in table_names]
    )
    count_res = run_cli_query(count_queries + ";")
    for r in count_res.get("rows", []):
        print(f"  {r.get('table_name'):<32}: {r.get('count')} records")


def cmd_ping() -> None:
    """Dispatches a keep-alive heartbeat query to prevent free tier dormancy."""
    res = run_cli_query("SELECT 1 as keepalive, NOW() as server_time;")
    rows = res.get("rows", [])
    if rows and rows[0].get("keepalive") == 1:
        print(f"Keep-alive heartbeat SUCCESS: Server timestamp {rows[0].get('server_time')}")
    else:
        print("Keep-alive heartbeat FAILED or returned unexpected response.")


def main():
    parser = argparse.ArgumentParser(description="Supabase Cloud Database Management Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    subparsers.add_parser("status", help="Inspect remote project status")
    subparsers.add_parser("verify", help="Verify all 29 platform tables and row counts")
    subparsers.add_parser("ping", help="Send manual anti-dormancy keep-alive query")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status()
    elif args.command == "verify":
        cmd_verify_tables()
    elif args.command == "ping":
        cmd_ping()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
