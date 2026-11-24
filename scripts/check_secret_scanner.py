"""Prove gitleaks catches a synthetic token, without using a real credential."""

from pathlib import Path
import secrets
import shutil
import string
import subprocess
import tempfile

scanner = shutil.which("gitleaks")
if scanner is None:
    raise SystemExit("Install gitleaks from its official release before this demonstration")
with tempfile.TemporaryDirectory() as directory:
    sample = "ghp_" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(36))
    (Path(directory) / "sample.txt").write_text("token=" + sample)
    result = subprocess.run([scanner, "dir", directory, "--redact", "--no-banner"], check=False)
    if result.returncode != 1:
        raise SystemExit("Expected gitleaks to reject the synthetic token")
print("PASS: synthetic token rejected; temporary file removed; no real credentials used")
