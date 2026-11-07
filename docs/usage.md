# Getting started

This guide takes a new machine from nothing to a first round: an AI agent that works one
TileOPs performance issue on one GPU and opens a pull request. Follow the steps in order.
Each step ends with a command that shows it worked.

In commands, replace each `<...>` with your own value: `<you>` is your GitHub login,
`<Op>` an op name from `topa hunt`, `<issue>` an issue number, `<slug>` a round name and
`<pane-id>` a herdr pane id.

<details open><summary><b>Contents</b></summary>

1. [What topa does](#what-topa-does)
2. [What you need](#what-you-need)
3. [Step 1: Set up Git and GitHub](#step-1-set-up-git-and-github)
4. [Step 2: Prepare the TileOPs and TileFoundry checkouts](#step-2-prepare-the-tileops-and-tilefoundry-checkouts)
5. [Step 3: Install topa](#step-3-install-topa)
6. [Step 4: Configure](#step-4-configure)
7. [Step 5: Run setup](#step-5-run-setup)
8. [Step 6: Start herdr](#step-6-start-herdr)
9. [Step 7: Pick an op and its issue](#step-7-pick-an-op-and-its-issue)
10. [Step 8: Start a round](#step-8-start-a-round)
11. [Step 9: Watch and steer the agent](#step-9-watch-and-steer-the-agent)
12. [Step 10: Finish the round](#step-10-finish-the-round)
13. [Run a command without an agent](#run-a-command-without-an-agent)
14. [Troubleshooting](#troubleshooting)

</details>

## What topa does

topa is a command-line tool. It starts Claude Code agents that make
[TileOPs](https://github.com/tile-ai/TileOPs) kernels faster, gives each agent its own GPU
container, and keeps a record of what each agent did.

| Term | Meaning |
| --- | --- |
| TileOPs | An open-source library of GPU operators ("ops") written in TileLang. |
| TileFoundry | A compiler front end. The agent uses it to analyze, measure and schedule a kernel before writing it. |
| nightly benchmark | TileOPs measures every op against other libraries each night on an H200. topa reads the newest result. |
| rival | For one op, the library that is fastest on the largest number of the op's workloads. |
| ratio | The geometric mean of rival time / TileOPs time, over the workloads the rival won. |
| behind | An op whose ratio is below 0.95. |
| round | One agent working one GitHub issue, with one GPU, one branch and one directory of evidence. |
| slug | The name of a round, such as `i2301-r1` (issue 2301, first round). `topa round start` prints it; `say`, `stop` and `log` take it. |
| herdr | A terminal workspace manager for AI coding agents ([Herdr TUI](https://herdr.dev/tui)). Each agent runs in a herdr pane. |

[How a round works](workflow.md) describes the stages of a round.

## What you need

| Requirement | Check it with |
| --- | --- |
| x86_64 Linux | `uname -m` prints `x86_64` |
| An NVIDIA GPU with a driver that supports CUDA 13.2 | the header of `nvidia-smi` shows `CUDA Version: 13.2` or higher |
| Docker with the NVIDIA runtime | `docker info \| grep -i runtimes` shows `nvidia` |
| Claude Code, logged in, with access to the model in `model` | `claude` starts without asking you to log in |
| GitHub CLI `gh` | `gh --version` |
| `git`, `ssh`, `ssh-keygen` | `git --version` |
| herdr TUI | `herdr agent --help` lists `start`, `read` and `attach`; install it with `curl -fsSL https://herdr.dev/install.sh \| sh` |
| uv | `uv --version` |

The nightly benchmark runs on H200, so `topa hunt` reports H200 results. A round on another
GPU measures on that GPU.

The agent runs Claude Code with `--dangerously-skip-permissions`. Its shell commands, other
than `git`, `gh`, `topa`, file operations and text tools, run inside the round's container.
`git` and `gh` run with your credentials, so the agent pushes to your fork and comments on
GitHub as you.

## Step 1: Set up Git and GitHub

The agent commits with your global Git identity, pushes over HTTPS, and runs `gh` inside
the round's container. Each needs one setting.

```bash
git config --global user.name "<Your Name>"
git config --global user.email "<you@example.com>"
gh auth login --insecure-storage    # keep the token in ~/.config/gh/hosts.yml
gh auth setup-git                   # let git push to github.com with that token
```

`--insecure-storage` is required. topa mounts `~/.config/gh` into the container, and a
token kept in the system keyring is not visible there.

Check:

```bash
gh auth status
```

The `Logged in` line must name `~/.config/gh/hosts.yml`, not `keyring`.

Fork `tile-ai/TileOPs` to your account, on GitHub or with:

```bash
gh repo fork tile-ai/TileOPs --clone=false
```

## Step 2: Prepare the TileOPs and TileFoundry checkouts

topa needs a local clone of each repository. It never switches the clone's branch: each
round gets its own worktree under `worktree_root`.

```bash
git clone https://github.com/tile-ai/TileOPs ~/TileOPs
git -C ~/TileOPs remote add fork https://github.com/<you>/TileOPs
git clone https://github.com/tile-ai/TileFoundry ~/TileFoundry
```

The TileOPs clone needs two remotes:

| Remote points at | Used for |
| --- | --- |
| `github.com/tile-ai/TileOPs` | the base of every round's branch |
| `github.com/<you>/TileOPs` | the branch `topa pr` pushes |

The remote names do not matter; topa finds each remote by its URL. Check them:

```bash
git -C ~/TileOPs remote -v
```

The TileFoundry clone needs a remote for `tile-ai/TileFoundry`. topa reads `main` from
the remote named `upstream`, or from `origin` when there is no `upstream`.

## Step 3: Install topa

```bash
git clone https://github.com/tile-ai/topa ~/topa
cd ~/topa
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e .
```

Put the `topa` command on your `PATH`. Add this line to your shell profile, so every
terminal you open later has it:

```bash
export PATH="$HOME/topa/.venv/bin:$PATH"
```

Check:

```bash
topa --version
```

## Step 4: Configure

Write the default settings file. The command overwrites an existing file:

```bash
mkdir -p ~/.topa
topa config --default > ~/.topa/config.toml
```

Open `~/.topa/config.toml` and change the settings in the first table. Leave the rest at
their defaults unless the second table says otherwise.

| Setting | Set it to |
| --- | --- |
| `tileops_repo` | the TileOPs clone from step 2 |
| `tilefoundry_repo` | the TileFoundry clone from step 2 |
| `worktree_root` | a directory for the rounds' TileOPs worktrees; topa creates it |
| `fork_owner` | your GitHub login; unset, topa asks `gh` for it |

| Setting | Default | Change it when |
| --- | --- | --- |
| `gpu_exclude` | `[4, 5]` | those cards are not reserved on your machine; `[]` uses every card |
| `docker_host` | unset: the `DOCKER_HOST` of your shell | Docker must be reached at another address |
| `docker_bootstrap` | unset | a script must start the Docker daemon before each round |
| `proxy_host` | `10.0.2.2` | see below |
| `model`, `effort` | `claude-opus-5-5`, `high` | you want the agent on another model or effort |

`proxy_host` matters only when `HTTP_PROXY` or `HTTPS_PROXY` points at `127.0.0.1` or
`localhost`. topa replaces that address with `proxy_host` inside the container. `10.0.2.2`
is how a rootless Docker container reaches the host. With rootful Docker, set it to the
host address on the Docker bridge, usually `172.17.0.1`, and make the proxy listen there.

`topa config` prints the settings in effect. `TOPA_<NAME>` in the environment overrides one
setting for one command, for example `TOPA_GPU=3 topa round start 2301`.

## Step 5: Run setup

```bash
topa setup
```

Setup checks the tools and the two clones, pulls `runner_image` (8.8 GB on disk), builds
the agent image `topa:agent` on it, and makes `~/.ssh/config` include the rounds' SSH
entries. It also marks `~/.topa/rounds` as trusted in `~/.claude.json`, so Claude Code
starts in a round directory without asking.

Setup stops at the first missing piece; fix it and run setup again. Run setup again after
you change `runner_image`, so `topa:agent` is rebuilt on the new image.

## Step 6: Start herdr

topa starts each agent in a herdr pane, so a herdr server must be running. Start it in a
terminal you keep open; `herdr server` runs it without the herdr interface:

```bash
herdr server
```

Check from another terminal that `herdr agent list` answers.

## Step 7: Pick an op and its issue

```bash
topa hunt
```

The first line names the nightly that was graded. The table lists every op that is behind:

| Column | Meaning |
| --- | --- |
| `op` | the op's name; pass it to `topa issue new` |
| `rival`, `ratio` | see [What topa does](#what-topa-does) |
| `behind` | how many of the op's workloads are behind, of those rated |
| `issue` | the open TileOPs issue that names the op, if any |
| `assignee` | who that issue is assigned to |
| `rounds` | rounds already working that issue |

An empty table means no op is behind in the newest nightly. `topa hunt --all` lists every
graded op, and `topa grade` prints the grade of each one.

To work an op, file or claim its issue. This writes to the public `tile-ai/TileOPs`
repository, so preview it first:

```bash
topa issue new <Op> --dry-run   # print the issue; file nothing
topa issue new <Op>
```

| Case | What `issue new` does |
| --- | --- |
| an open issue names the op and has no assignee | assigns it to you |
| an open issue names the op and someone has it | leaves it alone and prints its assignee |
| no open issue names the op | files a new issue assigned to you, with the label `perf`, under the tracker issue `tracker` |

It prints the issue number. Any open TileOPs issue can start a round; it does not have to
come from `topa hunt`.

## Step 8: Start a round

Preview first. This prints the slug, branch and paths, and changes nothing:

```bash
topa round start <issue> --dry-run
```

Then start it:

```bash
topa round start <issue>
```

The first round on an image also caches TileFoundry's extra dependencies. The command
prints the slug, the pane id and the commands to reach the round. Confirm that the agent started working:

```bash
herdr agent read <pane-id>
```

The output shows the agent reading `brief.md`. If it shows the prompt still sitting in the
input box, open the pane with `herdr agent attach <pane-id>` and press Enter. From then on
the agent works without further input.

## Step 9: Watch and steer the agent

| To | Run |
| --- | --- |
| see every round, its agent state and its PR | `topa round status` |
| read the agent's recent terminal output | `herdr agent read <pane-id>` |
| open the agent's terminal and type to it | `herdr agent attach <pane-id>` |
| send the agent an instruction | `topa round say <slug> "..."` |
| see when the round was created, started, messaged, stopped, and its PR | `topa round log <slug>` |

The pane id is printed by `round start` and stored in `~/.topa/rounds/<slug>/round.json`.

The agent's evidence and report are in `~/.topa/rounds/<slug>/`, and its code change in
`<worktree_root>/tileops-<slug>/`. [Layout](layout.md#on-the-machine) lists both.

## Step 10: Finish the round

A round ends in one of these ways. Each needs you to end it; a round keeps its GPU until
you do.

| Outcome | What the agent leaves | What you do |
| --- | --- | --- |
| PR open | a PR from your fork; `topa round status` shows it | send review comments with `topa round say`; the agent stays in its pane to answer CI and review |
| PR merged or closed | the PR on GitHub | `topa round stop <slug> --rm` |
| no improvement | `no improvement` in `report.md`, and no PR | read `report.md`, then `topa round stop <slug> --rm` |

Before `--rm`, check that nothing uncommitted is left in the worktree. `--rm` deletes the
worktree with any uncommitted change in it:

```bash
git -C <worktree_root>/tileops-<slug> status --short
```

`topa round stop <slug>` without `--rm` frees the GPU and keeps the worktree. topa has no
command that resumes a stopped round. [Layout](layout.md#on-the-machine) lists what each
form keeps.

## Run a command without an agent

`topa run` runs one command in a fresh container with one GPU, against a TileOPs worktree.
Use it to reproduce a failure or check a branch by hand:

```bash
cd ~/TileOPs
topa run -- python -m pytest tests/ops -k <Op>
topa run            # an interactive shell in the container
```

## Troubleshooting

| Message | Fix |
| --- | --- |
| `not a git checkout: <path>` | `tileops_repo` or `tilefoundry_repo` does not point at a clone; fix it in `~/.topa/config.toml` |
| `failed to resolve reference ... not found` during setup | `runner_image` names a tag that does not exist; set it to an image listed under `ghcr.io/tile-ai/tileops-dev` |
| `server_not_running` | start herdr ([step 6](#step-6-start-herdr)) |
| `<repo> has no remote for github.com/<owner>/TileOPs` | add the missing remote to the TileOPs clone ([step 2](#step-2-prepare-the-tileops-and-tilefoundry-checkouts)) |
| `the mounted GitHub credentials are not usable inside the container` | the gh token is in the keyring; run `gh auth login --insecure-storage` ([step 1](#step-1-set-up-git-and-github)), then `topa round stop <slug> --rm` and start again |
| `N rounds are live ...; max_rounds is N` | stop a round, raise `max_rounds`, or pass `--force` |
| `round <slug> already works #<issue>` | that issue already has a running round; use `topa round status` |
| `round <slug> failed to start` | read the error above it, fix it, then run `topa round stop <slug> --rm` before starting again |
| `no usable GPU` | every card is in `gpu_exclude` or in Exclusive_Process compute mode; shrink `gpu_exclude`, or have an administrator set a card to Default mode (`nvidia-smi -c DEFAULT -i <index>`) |
| `warning: ... sharing gpu N` | no free card was left, so the round shares one; its timings may be noisy |
| `topa round say` reports the agent did not start a new turn | open the pane with `herdr agent attach <pane-id>` and check the input box |
