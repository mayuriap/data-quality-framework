import json
from pathlib import Path

suites_dir = Path("great_expectations/expectations")

for suite_file in suites_dir.glob("*.json"):
    # Get suite name from filename
    suite_name = suite_file.stem  # e.g. "bronze_customers_suite"
    
    with open(suite_file, "r") as f:
        suite = json.load(f)
    
    # Fix each expectation
    fixed_expectations = []
    for exp in suite.get("expectations", []):
        exp.pop("id", None)
        if "expectation_type" in exp and "type" not in exp:
            exp["type"] = exp.pop("expectation_type")
        fixed_expectations.append(exp)
    
    # Rebuild suite cleanly
    clean_suite = {
        "name": suite_name,
        "expectations": fixed_expectations,
        "meta": suite.get("meta", {})
    }
    
    with open(suite_file, "w") as f:
        json.dump(clean_suite, f, indent=2)
    
    print(f"Fixed: {suite_file.name} — name={suite_name}")

print("All suites fixed")