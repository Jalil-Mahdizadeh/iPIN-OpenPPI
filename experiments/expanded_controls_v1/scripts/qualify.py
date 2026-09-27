"""Run independent semantic oracles before fitting/scoring."""
import sys
import os
from pathlib import Path
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
import pytest
from control_io import OUT, cuda, now, record, write
from macro_metrics import qualify_macro


def main():
    device = cuda()
    code = pytest.main(["/tests", "-q", "-p", "no:cacheprovider", "--basetemp=/output/tmp/pytest"])
    if code:
        raise SystemExit(code)
    result = qualify_macro(device)
    filename = "QUALIFICATION_FINAL.json" if "--final" in sys.argv else "QUALIFICATION.json"
    write(OUT / filename, {
        "at_utc": now(), "unit_oracles_passed": True, "macro_bootstrap_oracle": result,
        "tests": [record(p) for p in sorted(Path("/tests").glob("*.py"))],
        "code": [record(p) for p in sorted(Path("/code").glob("*.py"))],
    })
    print({"qualification_complete": True, "macro": result}, flush=True)


if __name__ == "__main__":
    main()
