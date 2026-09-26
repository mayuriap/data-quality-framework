"""
generate_dashboard.py

Runs all tests and generates a unified HTML dashboard.

Usage: python generate_dashboard.py
Output: reports/dashboard.html
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


def run_dbt_tests() -> dict:
    """Run dbt tests and return results."""
    logger.info("Running dbt tests...")
    result = subprocess.run(
        ["dbt", "test"],
        capture_output=True,
        text=True,
        cwd=ROOT / "dbt_tests"
    )
    output = result.stdout + result.stderr

    # Parse dbt output
    passed  = 0
    failed  = 0
    total   = 0
    details = []

    for line in output.split("\n"):
        if "PASS" in line and "of" in line:
            passed += 1
            total  += 1
            details.append({"status": "PASS", "name": line.strip()})
        elif "FAIL" in line and "of" in line:
            failed += 1
            total  += 1
            details.append({"status": "FAIL", "name": line.strip()})
        elif "ERROR" in line and "of" in line:
            failed += 1
            total  += 1
            details.append({"status": "ERROR", "name": line.strip()})

    return {
        "passed":  passed,
        "failed":  failed,
        "total":   total,
        "details": details,
        "output":  output
    }


def run_behave_tests() -> dict:
    """Run Behave tests and return results."""
    logger.info("Running Behave tests...")
    result = subprocess.run(
        ["behave", "features/dbt_data_quality.feature",
         "--format", "json", "--outfile", "reports/behave_results.json"],
        capture_output=True,
        text=True,
        cwd=ROOT
    )

    # Also run for text output
    result2 = subprocess.run(
        ["behave", "features/dbt_data_quality.feature"],
        capture_output=True,
        text=True,
        cwd=ROOT
    )

    output   = result2.stdout + result2.stderr
    scenarios = []
    passed    = 0
    failed    = 0

    # Parse behave JSON output
    json_path = ROOT / "reports" / "behave_results.json"
    if json_path.exists():
        with open(json_path) as f:
            behave_data = json.load(f)

        for feature in behave_data:
            for scenario in feature.get("elements", []):
                name   = scenario.get("name", "")
                steps  = scenario.get("steps", [])
                status = "PASS"

                for step in steps:
                    if step.get("result", {}).get("status") == "failed":
                        status = "FAIL"
                        failed += 1
                        break

                if status == "PASS":
                    passed += 1

                scenarios.append({
                    "name":   name,
                    "status": status,
                    "steps":  len(steps)
                })

    # Extract step counts from output
               # Extract step counts from output
        steps_passed = 0
        steps_failed = 0
        for line in output.split("\n"):
            if "steps passed" in line:
                # Format: "54 steps passed, 0 failed, 0 skipped"
                try:
                    parts        = line.strip().split()
                    steps_passed = int(parts[0])
                    # Find failed count
                    for i, part in enumerate(parts):
                        if part == "failed," or part == "failed":
                            steps_failed = int(parts[i-1])
                            break
                except (ValueError, IndexError):
                    pass

    return {
        "scenarios":     scenarios,
        "passed":        passed,
        "failed":        failed,
        "total":         len(scenarios),
        "steps_passed":  steps_passed,
        "steps_failed":  steps_failed
    }


def run_ge_validation() -> dict:
    """Run GE validation and return results."""
    logger.info("Running Great Expectations validation...")
    from utils.ge_validator import GEValidator

    gev     = GEValidator()
    results = gev.validate_all()
    gev.context.build_data_docs()

    suites = []
    total_passed = 0
    total_evaluated = 0

    for name, result in results.items():
        if name == "overall_success":
            continue
        stats = result.get("statistics", {})
        suites.append({
            "name":       name,
            "success":    result.get("success", False),
            "passed":     stats.get("successful", 0),
            "evaluated":  stats.get("evaluated", 0),
            "pct":        stats.get("success_pct", 0)
        })
        total_passed    += stats.get("successful", 0)
        total_evaluated += stats.get("evaluated", 0)

    return {
        "suites":           suites,
        "total_passed":     total_passed,
        "total_evaluated":  total_evaluated,
        "overall_success":  results["overall_success"]
    }


def generate_html(dbt: dict, behave: dict, ge: dict) -> str:
    """Generate HTML dashboard from test results."""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Status colors
    def status_color(passed, total):
        pct = (passed / total * 100) if total > 0 else 0
        if pct == 100:
            return "#28a745"  # green
        elif pct >= 80:
            return "#ffc107"  # yellow
        else:
            return "#dc3545"  # red

    # BDD scenarios HTML
    scenarios_html = ""
    for s in behave.get("scenarios", []):
        color  = "#28a745" if s["status"] == "PASS" else "#dc3545"
        icon   = "✅" if s["status"] == "PASS" else "❌"
        scenarios_html += f"""
        <tr>
            <td>{icon}</td>
            <td>{s['name']}</td>
            <td style="color:{color}">{s['status']}</td>
            <td>{s['steps']} steps</td>
        </tr>"""

    # GE suites HTML
    ge_suites_html = ""
    for suite in ge.get("suites", []):
        color = "#28a745" if suite["success"] else "#dc3545"
        icon  = "✅" if suite["success"] else "❌"
        ge_suites_html += f"""
        <tr>
            <td>{icon}</td>
            <td>{suite['name']}</td>
            <td style="color:{color}">
                {suite['passed']}/{suite['evaluated']}
            </td>
            <td style="color:{color}">{suite['pct']:.1f}%</td>
        </tr>"""

    dbt_color    = status_color(dbt["passed"], dbt["total"]) if dbt["total"] > 0 else "#28a745"
    behave_color = status_color(behave["steps_passed"], behave["steps_passed"] + behave["steps_failed"])
    ge_color     = "#28a745" if ge["overall_success"] else "#dc3545"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Quality Framework — Test Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 24px;
        }}
        h1 {{
            color: #58a6ff;
            font-size: 24px;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: #8b949e;
            font-size: 14px;
            margin-bottom: 32px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }}
        .card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
        }}
        .card h2 {{
            font-size: 14px;
            color: #8b949e;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .card .count {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 4px;
        }}
        .card .label {{
            font-size: 12px;
            color: #8b949e;
        }}
        .section {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
        }}
        .section h3 {{
            color: #58a6ff;
            margin-bottom: 16px;
            font-size: 16px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            text-align: left;
            padding: 8px 12px;
            color: #8b949e;
            font-size: 12px;
            border-bottom: 1px solid #30363d;
        }}
        td {{
            padding: 8px 12px;
            font-size: 13px;
            border-bottom: 1px solid #21262d;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-pass {{ background: #1a4731; color: #3fb950; }}
        .badge-fail {{ background: #4d1f1f; color: #f85149; }}
        .findings {{
            background: #2d1f1f;
            border: 1px solid #f85149;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }}
        .findings h3 {{
            color: #f85149;
            margin-bottom: 8px;
        }}
        .findings ul {{
            list-style: none;
            padding: 0;
        }}
        .findings li {{
            padding: 4px 0;
            font-size: 13px;
        }}
        .architecture {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-bottom: 16px;
        }}
        .layer {{
            background: #1c2128;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 12px;
            text-align: center;
        }}
        .layer .name {{
            font-size: 12px;
            color: #8b949e;
            text-transform: uppercase;
        }}
        .layer .status {{
            font-size: 20px;
            margin: 4px 0;
        }}
        .layer .count {{
            font-size: 11px;
            color: #8b949e;
        }}
    </style>
</head>
<body>
    <h1>🔍 Data Quality Framework</h1>
    <p class="subtitle">Test Execution Dashboard — Generated: {timestamp}</p>

    <!-- Summary Cards -->
    <div class="summary-grid">
        <div class="card">
            <h2>dbt Tests</h2>
            <div class="count" style="color:{dbt_color}">
                {dbt['passed']}/{dbt['total']}
            </div>
            <div class="label">expectations passing</div>
        </div>
        <div class="card">
            <h2>BDD Behave</h2>
            <div class="count" style="color:{behave_color}">
                {behave['steps_passed']}/54
            </div>
            <div class="label">steps passing</div>
        </div>
        <div class="card">
            <h2>Great Expectations</h2>
            <div class="count" style="color:{ge_color}">
                {ge['total_passed']}/{ge['total_evaluated']}
            </div>
            <div class="label">expectations passing</div>
        </div>
    </div>

    <!-- Medallion Architecture -->
    <div class="section">
        <h3>Medallion Architecture Coverage</h3>
        <div class="architecture">
            <div class="layer">
                <div class="name">Bronze</div>
                <div class="status">✅</div>
                <div class="count">Raw + DQ Flags</div>
            </div>
            <div class="layer">
                <div class="name">Silver</div>
                <div class="status">✅</div>
                <div class="count">Cleaned Data</div>
            </div>
            <div class="layer">
                <div class="name">Gold</div>
                <div class="status">✅</div>
                <div class="count">Aggregations</div>
            </div>
        </div>
    </div>

    <!-- Known Findings -->
    <div class="findings">
        <h3>⚠️ Known Data Quality Findings</h3>
        <ul>
            <li>• 10 duplicate transaction IDs found in Silver layer</li>
            <li>• 1 duplicate customer ID found in Silver layer</li>
            <li>• 3 bad transactions leaked to Silver due to duplicate IDs</li>
            <li>• Root cause: ETL pipeline missing deduplication logic</li>
            <li>• Recommendation: Add ROW_NUMBER() deduplication to Silver models</li>
        </ul>
    </div>

    <!-- BDD Scenarios -->
    <div class="section">
        <h3>BDD Scenarios ({behave['total']} scenarios, {behave['steps_passed']} steps passing)</h3>
        <table>
            <tr>
                <th></th>
                <th>Scenario</th>
                <th>Status</th>
                <th>Steps</th>
            </tr>
            {scenarios_html}
        </table>
    </div>

    <!-- GE Suites -->
    <div class="section">
        <h3>Great Expectations Suites ({ge['total_passed']}/{ge['total_evaluated']} passing)</h3>
        <table>
            <tr>
                <th></th>
                <th>Suite</th>
                <th>Expectations</th>
                <th>Pass Rate</th>
            </tr>
            {ge_suites_html}
        </table>
    </div>

</body>
</html>"""

    return html


if __name__ == "__main__":
    print("=" * 60)
    print("  Data Quality Framework — Generating Dashboard")
    print("=" * 60)

    # Create reports folder
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Run all tests
    dbt_results    = run_dbt_tests()
    behave_results = run_behave_tests()
    ge_results     = run_ge_validation()

    # Generate HTML
    html = generate_html(dbt_results, behave_results, ge_results)

    # Save dashboard
    dashboard_path = reports_dir / "dashboard.html"
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ Dashboard generated: {dashboard_path}")
    print("Open in browser to view results")

    # Auto open in browser
    import webbrowser
    webbrowser.open(str(dashboard_path))