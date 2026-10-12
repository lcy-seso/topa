"""Run once in the agent image: stage what TileFoundry needs beyond the runner.

Usage: python stage_tilefoundry.py <pyproject.toml> <out-dir>

The runner already carries the compute stack, so a round installs as little as it
can, offline, and changes nothing the runner has:

- `out/wheels/`: exact wheels of the TileFoundry dependencies the runner lacks, and
  of what they need that the runner lacks too. Resolved against the installed
  packages, so nothing the runner has is downloaded again.
- `out/build-tools/`: TileFoundry's build backend, reached by PYTHONPATH, so the
  editable install needs no network and leaves the runner's setuptools alone.
- `out/report.json`: what was staged, and the dependencies the runner has at a
  version TileFoundry does not ask for. Those keep the runner's version.
"""

import importlib.metadata as metadata
import json
import subprocess
import sys
import tomllib
from pathlib import Path

try:
    from packaging.requirements import Requirement
except ImportError:  # pip always carries a copy
    from pip._vendor.packaging.requirements import Requirement

PIP = [sys.executable, "-m", "pip", "--quiet", "--disable-pip-version-check"]

pyproject, out = Path(sys.argv[1]), Path(sys.argv[2])
with pyproject.open("rb") as handle:
    data = tomllib.load(handle)
declared = data["project"].get("dependencies", [])
backend = data["build-system"]["requires"]

missing, mismatched = [], []
for text in declared:
    requirement = Requirement(text)
    if requirement.marker and not requirement.marker.evaluate():
        continue
    try:
        version = metadata.version(requirement.name)
    except metadata.PackageNotFoundError:
        missing.append(text)
        continue
    if not requirement.specifier.contains(version, prereleases=True):
        mismatched.append(f"{requirement.name} {version} (TileFoundry wants {requirement.specifier})")

wheels = out / "wheels"
wheels.mkdir(parents=True, exist_ok=True)
pins = []
if missing:
    plan = out / "plan.json"
    subprocess.run([*PIP, "install", "--dry-run", "--report", str(plan),
                    *missing], check=True)
    for item in json.loads(plan.read_text())["install"]:
        pins.append(f"{item['metadata']['name']}=={item['metadata']['version']}")
    subprocess.run([*PIP, "download", "--no-deps", "--only-binary=:all:", "--dest", str(wheels), *pins],
                   check=True)
subprocess.run([*PIP, "install", "--root-user-action=ignore", "--target", str(out / "build-tools"),
                *backend], check=True)
(out / "report.json").write_text(json.dumps(
    {"missing": missing, "staged": pins, "build_backend": backend, "mismatched": mismatched}, indent=2) + "\n")
