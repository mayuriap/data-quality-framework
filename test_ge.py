from utils.ge_validator import GEValidator

gev     = GEValidator()
results = gev.validate_all()

for name, result in results.items():
    if name == "overall_success":
        print(f"\nOverall: {'PASS' if result else 'FAIL'}")
    else:
        status = "PASS" if result.get("success") else "FAIL"
        stats  = result.get("statistics", {})
        print(f"{status} {name}: {stats.get('successful')}/{stats.get('evaluated')} expectations")