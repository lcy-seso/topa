# Getting started

You need x86_64 Linux with an NVIDIA driver for CUDA 13.2 or newer, Docker with the NVIDIA
runtime, Claude Code (logged in), `gh`, `git`, `uv` and the
[herdr TUI](https://herdr.dev/tui).

## 1. Set up Git and GitHub

The agent commits, pushes and comments as you. The gh token must live in
`~/.config/gh/hosts.yml`, because the round container reads it from there.

```bash
git config --global user.name "<Your Name>"
git config --global user.email "<you@example.com>"
gh auth login --insecure-storage
gh auth setup-git
gh repo fork tile-ai/TileOPs --clone=false
```

## 2. Clone and install

```bash
git clone https://github.com/tile-ai/TileOPs ~/TileOPs
git -C ~/TileOPs remote add fork https://github.com/<you>/TileOPs
git clone https://github.com/tile-ai/TileFoundry ~/TileFoundry

git clone https://github.com/tile-ai/topa ~/topa && cd ~/topa
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e .
export PATH="$HOME/topa/.venv/bin:$PATH"
```

## 3. Configure

```bash
mkdir -p ~/.topa && topa config --default > ~/.topa/config.toml
```

Set `tileops_repo`, `tilefoundry_repo`, `worktree_root` and `fork_owner` in that file, and
`gpu_exclude` to the cards topa must not use. Then:

```bash
topa setup       # pulls the runner image and builds topa:agent
herdr server     # keep it running in its own terminal
```

## 4. Run a round

```bash
topa hunt                  # ops behind on the nightly, with their issues
topa issue new <Op>        # file or claim the op's issue on tile-ai/TileOPs
topa round start <issue>   # start an agent on it
```

The agent works on its own and opens a PR from your fork when it finds an improvement.
Follow it with `topa round status`, read its screen with `herdr agent read <pane-id>`, and
send it instructions with `topa round say <slug> "..."`.

When the PR is merged or closed, or `report.md` says `no improvement`, end the round:

```bash
topa round stop <slug> --rm
```

`--rm` deletes the round's worktree, including uncommitted changes.

Other commands are in [Commands](commands.md); what topa keeps on disk is in
[Layout](layout.md).
