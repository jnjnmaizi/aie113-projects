"""Break only this Python process; leave the source file intact."""

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pytest
from bean_vision import domain

source = inspect.getsource(domain.decide)
assert "probabilities[best] < threshold" in source
broken = source.replace("probabilities[best] < threshold", "probabilities[best] > threshold")
namespace = dict(domain.__dict__)
exec(compile(broken, "deliberate-broken-rule", "exec"), namespace)
domain.decide = namespace["decide"]
print("Deliberately reversed the confidence rule IN MEMORY ONLY")
result = pytest.main([str(Path(__file__).resolve().parents[1] / "tests/test_domain.py"), "-q"])
if result != pytest.ExitCode.TESTS_FAILED:
    raise SystemExit("Expected tests to fail on the broken rule")
print("SUCCESS: the tests caught the deliberate defect; source files were unchanged")
