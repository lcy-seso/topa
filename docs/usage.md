# Getting started

From a new machine to a first round: one Claude Code agent working one
[TileOPs](https://github.com/tile-ai/TileOPs) issue on one GPU with
[TileFoundry](https://github.com/tile-ai/TileFoundry). [How a round works](workflow.md)
explains the stages. Replace each `<...>` with your own value.

## Requirements

| Requirement | Check |
| --- | --- |
| x86_64 Linux, NVIDIA driver for CUDA 13.2 or newer | the `nvidia-smi` header shows `CUDA Version: 13.2` or higher |
| Docker with the NVIDIA runtime | `docker info \| grep -i runtimes` shows `nvidia` |
| Claude Code, logged in | `claude` starts without a login prompt |
| `gh`, `git`, `ssh`, `uv` | each answers `--version` |
| [herdr TUI](https://herdr.dev/tui) | `curl -fsSL https://herdr.dev/install.sh \| sh` installs it |

## 1. Git and GitHub

The agent commits, pushes and comments on GitHub as you.

```bash
git config --global user.name "<Your Name>"
git config --global user.email "<you@example.com>"
gh auth login --insecure-storage   # the round container reads the token from ~/.config/gh/hosts.yml
gh auth setup-git                  # git pushes to github.com with that token
gh repo fork tile-ai/TileOPs --clone=false
```

## 2. Clone TileOPs and TileFoundry

```bash
git clone https://github.com/tile-ai/TileOPs ~/TileOPs
git -C ~/TileOPs remote add fork https://github.com/<you>/TileOPs
git clone https://github.com/tile-ai/TileFoundry ~/TileFoundry
```

topa finds the `tile-ai` and fork remotes by URL. Each round works in its own worktree, so
the clones stay on their branch.

## 3. Install and configure topa

```bash
git clone https://github.com/tile-ai/topa ~/topa && cd ~/topa
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e .
export PATH="$HOME/topa/.venv/bin:$PATH"   # add this line to your shell profile too
mkdir -p ~/.topa && topa config --default > ~/.topa/config.toml
```

In `~/.topa/config.toml`, set `tileops_repo`, `tilefoundry_repo`, `worktree_root` and
`fork_owner`. Two more settings depend on the machine:

| Setting | Change it when |
| --- | --- |
| `gpu_exclude = [4, 5]` | those cards are free to use on your machine |
| `proxy_host = "10.0.2.2"` | `HTTPS_PROXY` points at `127.0.0.1` and Docker is rootful; set the host's Docker bridge address, usually `172.17.0.1` |

`topa config` prints the settings in effect. `TOPA_<NAME>=<value>` overrides one setting
for one command.

## 4. Run setup and herdr

```bash
topa setup
herdr server   # in a terminal you keep open
```

Setup pulls `runner_image` (8.8 GB on disk) and builds `topa:agent` on it. It stops at the
first missing piece; fix it and rerun. topa starts each agent in a herdr pane, so the herdr
server must run whenever a round starts.

## 5. Pick an issue

```bash
topa hunt                       # ops behind on the newest nightly, with their issues
topa issue new <Op> --dry-run   # preview
topa issue new <Op>             # file or claim the op's issue on tile-ai/TileOPs
```

`issue new` assigns you an unassigned issue that names the op, leaves an issue someone else
holds, and otherwise files a new public issue. Any open TileOPs issue can start a round.

## 6. Run a round

```bash
topa round start <issue>   # prints the slug and the pane id
```

The agent then works on its own. Its evidence is in `~/.topa/rounds/<slug>/` and its code
change in `<worktree_root>/tileops-<slug>/`.

| To | Run |
| --- | --- |
| list rounds, agent states and PRs | `topa round status` |
| read the agent's screen | `herdr agent read <pane-id>` |
| type to the agent | `herdr agent attach <pane-id>` |
| send it an instruction | `topa round say <slug> "..."` |

## 7. End a round

A round holds its GPU until you stop it.

| Outcome | Do |
| --- | --- |
| PR open | pass review comments with `topa round say`; the agent answers CI and review |
| PR merged or closed, or `no improvement` in `report.md` | `topa round stop <slug> --rm` |

`--rm` deletes the worktree with any uncommitted change, so check
`git -C <worktree_root>/tileops-<slug> status` first. Without `--rm`, `stop` frees the GPU
and keeps the worktree. A stopped round cannot resume.

## Troubleshooting

Most errors name their fix. These do not:

| Message | Fix |
| --- | --- |
| `the mounted GitHub credentials are not usable inside the container` | the gh token is in the keyring: `gh auth login --insecure-storage`, then `topa round stop <slug> --rm` and start again |
| `failed to resolve reference` during setup | `runner_image` names a missing tag; pick one under `ghcr.io/tile-ai/tileops-dev` |
| `no usable GPU` | every card is in `gpu_exclude` or in Exclusive_Process mode; shrink `gpu_exclude`, or have an administrator run `nvidia-smi -i <index> -c DEFAULT` |
