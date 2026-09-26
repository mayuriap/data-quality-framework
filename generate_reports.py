"""
generate_reports.py

Generates all test reports:
1. dbt test results
2. Behave BDD results
3. Great Expectations Data Docs

Run: python generate_reports.py
"""

import os
import sys
import subprocess
from pathlib import Path
from loguru import logger

# Project root
ROOT = Path(__file__).parent

def create_reports_folder():
    """Create reports folder if not exists."""
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    logger.info(f"Reports folder: {reports_dir}")
    return reports_dir


def run_dbt_tests(reports_dir: Path):
    """Run dbt tests and save results."""
    logger.info("Running dbt tests...")
    
    result = subprocess.run(
        ["dbt", "test"],
        capture_output = True,
        text           = True,
        cwd            = ROOT / "dbt_tests"
    )
    
    output = result.stdout + result.stderr
    report_path = reports_dir / "dbt_test_results.txt"
    
    with open(report_path, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("DBT TEST RESULTS\n")
        f.write("=" * 60 + "\n")
        f.write(output)
    
    passed = "ERROR" not in output
    logger.info(f"dbt tests: {'PASS' if passed else 'KNOWN FINDINGS'}")
    logger.info(f"Report saved: {report_path}")
    return passed


def run_behave_tests(reports_dir: Path):
    """Run Behave BDD tests and save results."""
    logger.info("Running Behave tests...")
    
    result = subprocess.run(
        ["behave", "features/dbt_data_quality.feature"],
        capture_output = True,
        text           = True,
        cwd            = ROOT
    )
    
    output = result.stdout + result.stderr
    report_path = reports_dir / "behave_results.txt"
    
    with open(report_path, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("BEHAVE BDD TEST RESULTS\n")
        f.write("=" * 60 + "\n")
        f.write(output)
    
    logger.info(f"Behave report saved: {report_path}")
    return "steps passed" in output


def run_ge_validation(reports_dir: Path):
    """Run GE validation and generate Data Docs."""
    logger.info("Running Great Expectations validation...")
    
    sys.path.insert(0, str(ROOT))
    from utils.ge_validator import GEValidator
    
    gev     = GEValidator()
    results = gev.validate_all()
    
    # Generate HTML Data Docs
    gev.context.build_data_docs()
    
    # Save GE summary to text file
    report_path = reports_dir / "ge_validation_results.txt"
    with open(report_path, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("GREAT EXPECTATIONS VALIDATION RESULTS\n")
        f.write("=" * 60 + "\n")
        f.write(f"Overall: {'PASS' if results['overall_success'] else 'FAIL'}\n\n")
        
        for name, result in results.items():
            if name == "overall_success":
                continue
            stats  = result.get("statistics", {})
            status = "PASS" if result.get("success") else "FAIL"
            f.write(
                f"{status} {name}: "
                f"{stats.get('successful')}/{stats.get('evaluated')} "
                f"expectations ({stats.get('success_pct', 0):.1f}%)\n"
            )
    
    logger.info(f"GE report saved: {report_path}")
    logger.info("GE Data Docs generated at: great_expectations/uncommitted/data_docs/local_site/index.html")
    return results["overall_success"]


if __name__ == "__main__":
    print("=" * 60)
    print("  Generating all test reports")
    print("=" * 60)
    
    reports_dir = create_reports_folder()
    
    dbt_passed    = run_dbt_tests(reports_dir)
    behave_passed = run_behave_tests(reports_dir)
    ge_passed     = run_ge_validation(reports_dir)
    
    print("\n" + "=" * 60)
    print("  REPORT SUMMARY")
    print("=" * 60)
    print(f"  dbt tests:          {'PASS' if dbt_passed else 'KNOWN FINDINGS'}")
    print(f"  Behave BDD tests:   {'PASS' if behave_passed else 'FAIL'}")
    print(f"  GE validation:      {'PASS' if ge_passed else 'FAIL'}")
    print("=" * 60)
    print(f"\nReports saved to: {reports_dir}")
    print("GE HTML report:   great_expectations/uncommitted/data_docs/local_site/index.html")