# Getting started

This guide takes a new machine from nothing to a first round: an AI agent that works one
TileOPs performance issue on one GPU and opens a pull request. Follow the steps in order.
Each step ends with a command that shows it worked.

<details open><summary><b>Contents</b></summary>

1. [What topa does](#what-topa-does)
2. [What you need](#what-you-need)
3. [Step 1: Prepare the TileOPs and TileFoundry checkouts](#step-1-prepare-the-tileops-and-tilefoundry-checkouts)
4. [Step 2: Install topa](#step-2-install-topa)
5. [Step 3: Configure](#step-3-configure)
6. [Step 4: Run setup](#step-4-run-setup)
7. [Step 5: Start herdr](#step-5-start-herdr)
8. [Step 6: Pick an op and its issue](#step-6-pick-an-op-and-its-issue)
9. [Step 7: Start a round](#step-7-start-a-round)
10. [Step 8: Watch and steer the agent](#step-8-watch-and-steer-the-agent)
11. [Step 9: Finish the round](#step-9-finish-the-round)
12. [Run a command without an agent](#run-a-command-without-an-agent)
13. [Troubleshooting](#troubleshooting)

</details>

## What topa does

topa is a command-line tool. It starts Claude Code agents that make
[TileOPs](https://github.com/tile-ai/TileOPs) kernels faster, gives each agent its own GPU
container, and keeps a record of what each agent did.

| Term | Meaning |
| --- | --- |
| TileOPs | An open-source library of GPU operators ("ops") written in TileLang. |
| TileFoundry | A compiler front end. The agent uses it to analyze, measure and schedule a kernel before writing it. |
| nightly benchmark | TileOPs measures every op against other libraries each night. topa reads the newest result. |
| behind | An op whose geometric-mean speed is below 0.95x of its fastest rival. |
| round | One agent working one GitHub issue, with one GPU, one branch and one directory of evidence. |
| slug | The name of a round, such as `i2301-r1` (issue 2301, first round). Every `topa round` command takes it. |
| herdr | A terminal workspace manager for AI coding agents ([herdr.dev](https://herdr.dev)). Each agent runs in a herdr pane. |

A round goes through these stages:

1. `topa hunt` lists the ops that are behind.
2. `topa issue new <Op>` files a GitHub issue for an op, or claims an existing one.
3. `topa round start <issue>` prepares a branch, a container and a brief, then starts the
   agent.
4. The agent works on its own and opens a PR from your fork with `topa pr`.
5. `topa round stop <slug> --rm` ends the round and frees its resources.

[How a round works](workflow.md) describes what happens inside each stage.

## What you need

| Requirement | Check it with |
| --- | --- |
| Linux with an NVIDIA GPU (the nightly runs on H200) | `nvidia-smi -L` |
| Docker with the NVIDIA runtime | `docker info \| grep -i runtimes` shows `nvidia` |
| Claude Code, logged in | `claude` starts without asking you to log in |
| GitHub CLI, logged in | `gh auth status` |
| A fork of `tile-ai/TileOPs` on your GitHub account | `gh repo view <you>/TileOPs` |
| `git`, `ssh`, `ssh-keygen` | `git --version` |
| herdr | `herdr --version` |
| uv | `uv --version` |

The agent runs Claude Code with `--dangerously-skip-permissions`. Its shell commands, other
than `git`, `gh`, `topa`, file operations and text tools, run inside the round's container.
`git` and `gh` run on the host with your credentials, so the agent can push to your fork
and comment on GitHub as you.

## Step 1: Prepare the TileOPs and TileFoundry checkouts

topa needs a local clone of each repository. It never changes the clone's checked-out
branch; it adds worktrees next to it.

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

## Step 2: Install topa

```bash
git clone https://github.com/tile-ai/topa ~/topa
cd ~/topa
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e .
```

Put the `topa` command on your `PATH`, or call it as `~/topa/.venv/bin/topa`:

```bash
export PATH="$HOME/topa/.venv/bin:$PATH"
topa --version
```

## Step 3: Configure

Write the default settings file and open it:

```bash
mkdir -p ~/.topa
topa config --default > ~/.topa/config.toml
```

Change the settings in the first table. Leave the rest at their defaults unless the
second table says otherwise.

| Setting | Set it to |
| --- | --- |
| `tileops_repo` | the TileOPs clone from step 1 |
| `tilefoundry_repo` | the TileFoundry clone from step 1 |
| `worktree_root` | a directory for the rounds' TileOPs worktrees; topa creates it |
| `fork_owner` | your GitHub login; unset, topa asks `gh` for it |

| Setting | Default | Change it when |
| --- | --- | --- |
| `gpu` | unset: topa picks the least used card | every round must use one card |
| `gpu_exclude` | `[4, 5]` | those indexes are not reserved on your machine; set `[]` to use every card |
| `max_rounds` | `2` | you want more rounds running at the same time |
| `runner_image` | the public TileOPs dev image | TileOPs moves to a new image tag |
| `docker_host` | unset: Docker's own default | Docker listens somewhere other than `DOCKER_HOST` |
| `docker_bootstrap` | unset | a script must start the Docker daemon before each round |
| `proxy_host` | `10.0.2.2` | your HTTP proxy listens on `127.0.0.1` and Docker is not rootless; then set the host address the container can reach |
| `model`, `effort` | `claude-opus-5-5`, `high` | you want the agent on another model or effort |
| `tilefoundry_commit` | unset: the newest `main` | rounds must read one fixed TileFoundry commit |

`topa config` prints the settings in effect. `TOPA_<NAME>` in the environment overrides one
setting for one command, for example `TOPA_GPU=3 topa round start 2301`.

## Step 4: Run setup

```bash
topa setup
```

Setup checks the tools and the two clones, pulls `runner_image`, builds the agent image
`topa:agent` on it, and makes `~/.ssh/config` include the rounds' SSH entries. It also
marks `~/.topa/rounds` as trusted in `~/.claude.json`, so Claude Code starts in a round
directory without asking. The first run downloads several GB. A successful run ends like
this:

```text
built topa:agent on ghcr.io/tile-ai/tileops-dev:cuda13.2-torch2.13-tilelang0.1.12
added Include "/home/<you>/.topa/ssh-config/*" to /home/<you>/.ssh/config
marked /home/<you>/.topa/rounds as trusted in ~/.claude.json
```

Run setup again after you change `runner_image`.

## Step 5: Start herdr

topa opens each agent in a herdr pane, so a herdr server must be running. Start herdr in a
terminal you keep open, such as a tmux window:

```bash
herdr
```

Check from another terminal:

```bash
herdr agent list
```

An error with `server_not_running` means herdr is not running.

## Step 6: Pick an op and its issue

```bash
topa hunt
```

The first line names the nightly that was graded. The table lists every op that is behind:

| Column | Meaning |
| --- | --- |
| `op` | the op's name |
| `rival` | the library it is compared with |
| `ratio` | rival time / TileOPs time; below 0.95 is behind |
| `behind` | how many of the op's workloads are behind, of those rated |
| `issue` | the open TileOPs issue that names the op, if any |
| `assignee` | who that issue is assigned to |
| `rounds` | rounds already working that issue |

An empty table means no op is behind in the newest nightly. `topa hunt --all` lists every
graded op, and `topa grade` prints the grade of each one.

To work an op, file or claim its issue:

```bash
topa issue new <Op> --dry-run   # print the issue without filing it
topa issue new <Op>
```

`issue new` reuses an open issue that names the op. It assigns that issue to you when the
issue has no assignee, and leaves it alone when someone else has it. Otherwise it files a
new issue assigned to you. It prints the issue number.

Any open TileOPs issue can start a round; it does not have to come from `topa hunt`.

## Step 7: Start a round

Preview first. This prints the slug, branch and paths, and changes nothing:

```bash
topa round start <issue> --dry-run
```

Then start it:

```bash
topa round start <issue>
```

The command takes a few minutes the first time: it stages TileFoundry's dependencies in
the agent image. When it finishes it prints how to reach the round:

```text
round   i2301-r1  #2301  <branch>  gpu 2
dir     /home/<you>/.topa/rounds/i2301-r1
pane    <pane-id>
watch   herdr agent read <pane-id>
say     topa round say i2301-r1 "..."
stop    topa round stop i2301-r1 [--rm]
```

The agent now reads `brief.md` in the round directory and works without further input. A
round usually runs for hours.

At most `max_rounds` rounds run at the same time. `--force` starts one beyond the limit.

## Step 8: Watch and steer the agent

| To | Run |
| --- | --- |
| see every round, its agent state and its PR | `topa round status` |
| read the agent's recent terminal output | `herdr agent read <pane-id>` |
| open the agent's terminal and type to it | `herdr agent attach <pane-id>` |
| send the agent an instruction | `topa round say <slug> "..."` |
| see everything the round did | `topa round log <slug>` |

The pane id is printed by `round start` and stored in `~/.topa/rounds/<slug>/round.json`.

The round directory `~/.topa/rounds/<slug>/` holds the agent's work as it happens:

| Path | Contents |
| --- | --- |
| `brief.md` | the agent's instructions for this round |
| `environment.md` | the container, GPU, worktree and image of the round |
| `work/` | the HIR candidates, the runtime twin and the scheduled TIR |
| `evidence/` | raw correctness, benchmark and profile results |
| `report.md` | the agent's report, written at the end |
| `pr-template.md` | the PR title and body, filled in by the agent |

The production code change is in the round's TileOPs worktree,
`<worktree_root>/tileops-<slug>/`.

## Step 9: Finish the round

A round ends in one of two ways:

| Outcome | What the agent leaves |
| --- | --- |
| it found an improvement | a PR on `tile-ai/TileOPs` from your fork; `topa round status` shows it |
| it found none | `no improvement` in `report.md`, and no PR |

The agent opens the PR with `topa pr`. That command checks the evidence in the round
directory first and refuses to open a PR when something is missing. If the agent hit
TileFoundry problems, it also files one issue on `tile-ai/TileFoundry` and links it in
`report.md`.

After the PR is open, the agent stays in its pane to answer CI and review. Send it review
comments with `topa round say`.

When the PR is merged or abandoned, end the round:

```bash
topa round stop <slug>        # stop the agent and the container; keep everything else
topa round stop <slug> --rm   # also remove the container, the worktree and the checkout
```

Both copy the agent's transcripts into `~/.topa/rounds/<slug>/session/`. The round
directory itself is never deleted. [Layout](layout.md#on-the-machine) lists what each form
keeps.

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
| `server_not_running` | start herdr ([step 5](#step-5-start-herdr)) |
| `<repo> has no remote for github.com/<owner>/TileOPs` | add the missing remote to the TileOPs clone ([step 1](#step-1-prepare-the-tileops-and-tilefoundry-checkouts)) |
| `N rounds are live ...; max_rounds is N` | stop a round, raise `max_rounds`, or pass `--force` |
| `round <slug> already works #<issue>` | that issue already has a running round; use `topa round status` |
| `round <slug> failed to start` | read the error above it, fix it, then run `topa round stop <slug> --rm` before starting again |
| `no usable GPU` | every card is in `gpu_exclude` or in an exclusive compute mode; change `gpu_exclude` |
| `warning: ... sharing gpu N` | no free card was left, so the round shares one; its timings may be noisy |
| `topa round say` reports the agent did not start a new turn | open the pane with `herdr agent attach <pane-id>` and check the input box |
