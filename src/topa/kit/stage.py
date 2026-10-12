"""Run once in the agent image: stage what a round installs beyond the runner.

Usage: python stage.py <tilefoundry pyproject> <tileops pyproject> <out-dir>

The runner already carries the compute stack, so a round installs as little as it
can, offline, and changes nothing the runner has:

- `out/wheels/`: exact wheels of the TileFoundry dependencies the runner lacks, and
  of what they need that the runner lacks too. Resolved against the installed
  packages, so nothing the runner has is downloaded again.
- `out/build-tools/<project>/`: the build backend of TileFoundry and of TileOPs, each
  in its own directory and reached by PYTHONPATH, so both editable installs need no
  network and leave the runner's setuptools alone. TileOPs' runtime dependencies are
  the runner itself, so none are staged for it.
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

def load(path: str) -> dict:
    with open(path, "rb") as handle:
        return tomllib.load(handle)


tilefoundry, tileops, out = load(sys.argv[1]), load(sys.argv[2]), Path(sys.argv[3])
declared = tilefoundry["project"].get("dependencies", [])
backends = {name: data["build-system"]["requires"]
            for name, data in (("tilefoundry", tilefoundry), ("tileops", tileops))}

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
for name, requires in backends.items():
    subprocess.run([*PIP, "install", "--root-user-action=ignore", "--target", str(out / "build-tools" / name),
                    *requires], check=True)
(out / "report.json").write_text(json.dumps(
    {"missing": missing, "staged": pins, "build_backends": backends, "mismatched": mismatched}, indent=2) + "\n")
