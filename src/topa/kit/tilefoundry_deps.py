"""Run in a round container: which TileFoundry dependencies the runner lacks.

Prints JSON with `missing` (requirements no installed package satisfies by name) and
`mismatched` (installed, but outside TileFoundry's range). The runner's compute stack
wins: a mismatched package keeps its runner version and is only reported.
"""

import importlib.metadata as metadata
import json
import sys
import tomllib

try:
    from packaging.requirements import Requirement
except ImportError:  # pip always carries a copy
    from pip._vendor.packaging.requirements import Requirement

with open(sys.argv[1], "rb") as handle:
    declared = tomllib.load(handle)["project"].get("dependencies", [])

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
print(json.dumps({"missing": missing, "mismatched": mismatched}))
