# Install

```bash
git clone https://github.com/tile-ai/topa ~/topa
cd ~/topa
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e .
mkdir -p ~/.topa
.venv/bin/topa config --default > ~/.topa/config.toml
```

Edit `~/.topa/config.toml`: the paths of the TileOPs and TileFoundry checkouts, your fork
(`fork_owner`) and the GPUs. Then build the agent image:

```bash
.venv/bin/topa setup
```

`topa setup` stops at the first missing piece; fix it and run setup again. `topa config`
prints the settings in effect. `TOPA_<NAME>` in the environment overrides one setting for
one command.

It needs x86_64 Linux, an NVIDIA driver that supports CUDA 13.2, `claude`, `docker` with
the NVIDIA runtime, `gh`, `git`, the herdr TUI, `ssh`, `nvidia-smi` and `uv`. `gh` must keep
its token in `~/.config/gh/hosts.yml` (`gh auth login --insecure-storage`) and `git` must
push with it (`gh auth setup-git`). The TileOPs checkout needs a remote for
`tile-ai/TileOPs` and one for your fork. A herdr server must be running when a round
starts.

[Getting started](usage.md) walks through each of these with the command that checks it.
