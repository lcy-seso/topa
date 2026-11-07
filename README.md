# TOPA

**T**ileFoundry and Tile**O**ps: a **P**ath to **A**utonomous kernel engineering.

Agents build TileOps kernels with TileFoundry. Every kernel improves TileFoundry, and every TileFoundry improvement speeds up the next kernel.

## Quick start

```bash
git clone https://github.com/tile-ai/topa ~/topa && cd ~/topa
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e .
export PATH="$HOME/topa/.venv/bin:$PATH"
mkdir -p ~/.topa && topa config --default > ~/.topa/config.toml   # then set tileops_repo, tilefoundry_repo, fork_owner
topa setup                                     # pulls the runner image, builds topa:agent
herdr                                          # in its own terminal; keep it running
topa hunt                                      # ops that are behind, with their issues
topa round start <issue>                       # one agent, one GPU, one issue
topa round status
```

Each line is explained in [Getting started](docs/usage.md).

## Docs

- [Getting started](docs/usage.md): from a new machine to a first round, step by step
- [How a round works](docs/workflow.md): the loop, from the nightly benchmark to a PR
- [Install](docs/install.md): requirements, setup and configuration
- [Commands](docs/commands.md): every `topa` command
- [Layout](docs/layout.md): the repository, and what topa keeps on the machine
