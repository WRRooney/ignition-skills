---
name: ignition-setup
description: |
  Use when an agent needs a working `ign` CLI (package `ignition-gen-sdk`) against an Ignition 8.3 gateway: install, `.env` (IGNITION_URL, IGNITION_API_TOKEN, IGNITION_DATA_DIR), creating a gateway API token, verifying the connection, endpoint docs, choosing the API or data-dir write backend, and setting up `.ign_tools/` and `.agents/skills/ignition-local/`. Also use when `ign` reports "Auth error", "Network error", "Path error", or is missing from PATH.
  Positive triggers: "set up ign", "install ignition-gen-sdk", "connect to the gateway", "IGNITION_API_TOKEN", ".env for Ignition", "API token", "ign not found", "which backend", "data dir mounted", "openapi spec", "Generating API client".
  Do not trigger for: authoring tags or views (use ignition-tag / ignition-view), git tag, html tag, Ignition Designer installation, Java or gateway installation itself.
---

## What this skill covers

Getting from "a user has an Ignition 8.3 gateway" to "the agent can run `ign` verbs against it safely". Once setup is verified, the resource skills (`ignition-tag`, `ignition-provider`, `ignition-view`, ...) take over.

## 1. Install

Check first: if `ign --help` works, skip to step 2. Otherwise install it:

```bash
uv tool install git+https://github.com/WRRooney/ignition-gen-sdk    # preferred: isolated, puts `ign` on PATH
pip install git+https://github.com/WRRooney/ignition-gen-sdk        # alternative when uv is unavailable
ign --help                      # confirms the entry point
```

Python 3.12+ is required. `uv` downloads a matching Python if the machine lacks one; `pip` needs it installed already. If the machine has neither `uv` nor Python 3.12+, ask the user to install `uv` (https://docs.astral.sh/uv/) rather than installing it yourself. If `ign` installed but is not found, `uv tool dir --bin` prints where it went: run it by full path, or `uv tool update-shell` and restart the shell. After a `pip` install, `python3 -m ignition_gen_sdk.cli <verb> ...` is the equivalent invocation.

The base install covers every verb, including the typed resource verbs (`provider`, `db-conn`, `alarm-journal`, `driver`): the OpenAPI client generator is a core dependency, and the first typed verb fetches the gateway's spec to `.ign/openapi.json` and generates the client by itself (a few seconds, one-time "Generating API client" line on stderr). Two optional extras remain:

| Extra | Needed for |
|---|---|
| `strict` | `ign api --strict` (deep OpenAPI validation of body, query and path params) |
| `runtime` | `ign view validate` (headless render of a Perspective page); also run `playwright install chrome` |

Add them when a verb asks (`uv tool install 'ignition-gen-sdk[strict,runtime] @ git+https://github.com/WRRooney/ignition-gen-sdk'`).

## 2. Configure the environment

`ign` reads process environment variables first, then a `.env` file in the current working directory. Run `ign` from the directory that holds `.env` (usually the user's project or the gateway data directory).

| Variable | Required | Meaning |
|---|---|---|
| `IGNITION_URL` | yes | Gateway base URL, e.g. `http://localhost:8088`. From a host shell use the host-mapped port, not a container-internal hostname. |
| `IGNITION_API_TOKEN` | yes | The full `<name>:<secret>` value shown once when the API key is created (step 3). Both halves; `ign` refuses a bare secret. |
| `IGNITION_DATA_DIR` | for disk writes | Gateway data directory, the one containing `config/resources/` and `projects/`. Unset means the current directory. |
| `IGNITION_PROJECT` | no | Default Perspective project (`Global`). |
| `IGNITION_TAG_PROVIDER` | no | Default tag provider (`default`). |
| `IGNITION_STATE_DIR` | no | SDK state directory (`./.ign`). |

Minimal `.env`:

```dotenv
IGNITION_URL=http://localhost:8088
IGNITION_API_TOKEN=agent:the-secret-from-the-gateway
IGNITION_DATA_DIR=/srv/ignition/data
IGNITION_PROJECT=Demo
IGNITION_TAG_PROVIDER=default
```

Add both to the project's `.gitignore` before anything else:

```
.env
.ign/
```

See `references/env-contract.md` for the full variable list and resolution rules.

## 3. Create the API key in the gateway

The agent cannot do this step; the user does it in the gateway web UI, signed in as an administrator. Walk them through all four parts. A key created with the defaults alone fails: it cannot write (403), and on a plain `http://` gateway it is refused outright (401).

1. **Create a security level for the key.** Go to Platform > Security > Levels and add a level, for example `ApiWrite`. Where it sits in the tree does not matter (it does not need to be under Authenticated); what matters is that the same level is assigned to the key (part 3) and checked in Gateway Write Permissions (part 2).
2. **Give that level write access.** Go to Platform > Security > General Settings. Under Gateway Write Permissions, check `ApiWrite`, keep the levels already checked there (so administrators keep write access), and choose "AnyOf" (match at least one). Save. Write access includes read access.
3. **Create the key.** Go to Platform > Security > API Keys and click Create API Key +:
   - API Key Type: Basic Token.
   - Name: for example `agent`. The name becomes the first half of the token.
   - Require secure connections for API Keys: leave it on when `IGNITION_URL` is `https://`. Turn it off when the gateway is reached over plain `http://` (typical for a local or dev gateway), or every call returns 401.
   - Security levels: Authenticated is preselected and cannot be removed. Also check `ApiWrite`.
   - Save.
4. **Copy the key right away.** The gateway shows it only once and cannot show it again; if it is lost, delete the key and create a new one. Copy the whole value exactly as shown: it starts with the key name and a colon (`agent:...`). Put it in `.env` as `IGNITION_API_TOKEN=agent:...`.

Never ask the user to paste the key into chat. Ask them to write it into `.env` themselves, or to export it in the shell that launches the agent.

## 4. Verify

Run these in order. Each one proves one layer.

```bash
ign api GET /data/api/v1/gateway-info   # network + URL + token; first run also fetches the spec to .ign/openapi.json
ign provider names                      # a typed read verb: generates the client on first use, lists tag providers
ign openapi docs                        # renders .ign/api_reference/*.md (INDEX.md, AUTH.md, one file per endpoint group)
```

The spec is fetched automatically the first time anything needs it; `ign openapi fetch` exists only to refresh it after a gateway upgrade (it prints the path count and gateway version, which is a handy check on its own).

Error output follows one contract: an `Error:` line plus a `Hint:` line on stderr, exit code 1. Surface both verbatim to the user. Common mappings:

| Output | Meaning | Fix |
|---|---|---|
| `Auth error` | 401: token missing, malformed or refused | `.env` not in cwd; token is not the full `name:secret`; or the key requires secure connections while `IGNITION_URL` is `http://` (step 3) |
| `Permission error` | 403: the key cannot write | the key's security level is not in Gateway Write Permissions, or the key lacks that level (step 3, parts 1 to 3) |
| `Network error` | cannot reach `IGNITION_URL` (also fails the first-run spec fetch) | wrong port or container-internal hostname used from the host |
| `Path error` | path not in the cached spec | check `.ign/api_reference/INDEX.md`; `ign openapi fetch` if the gateway was upgraded |

`ign openapi docs` is the endpoint reference for `ign api` work. Read `.ign/api_reference/INDEX.md` before calling a raw endpoint.

## 5. Determine the write backend

`ign` has two ways to write to the gateway. Which one is available depends on whether the agent's shell can see the gateway data directory.

| Backend | How it writes | Used by |
|---|---|---|
| API | HTTP calls to `/data/api/v1/*`; changes register live | `tag push --backend api`, `tag import`, `provider`, `db-conn`, `alarm-journal`, `api` |
| Data dir + scan | Writes `config/resources/**` or `projects/**` files, then POSTs `/scan/config` or `/scan/projects` | `tag udt-type`, `tag udt-instance`, `tag set-udt-*`, `tag delete`, `view`, `page`, `script`, `named-query`, `style-class`, `stylesheet`, `theme`, `tag push --backend disk` |

To tell which the user has:

```bash
ls "$IGNITION_DATA_DIR/config/resources" "$IGNITION_DATA_DIR/projects"
```

If both directories list, disk writes are available. If not (typical when the gateway runs in a container or on another host without a mount), the agent has API-only access: tags, providers, database connections and raw API calls work; UDT type definitions and every Perspective resource do not. Tell the user what is unavailable rather than working around it. Details in `references/write-backends.md`.

## 6. Hard rules

These are not style preferences. They protect the gateway and the token.

1. `ign` is the sole writer of Ignition files. Never create or edit anything under `config/resources/**` or `projects/**` with an editor, a heredoc, `sed`, `cp`, or a Python script. The models in `ignition_gen_sdk` are the only sanctioned serializer.
2. No `curl`, `wget`, `httpx`, or `requests` against the gateway. Use `ign api METHOD PATH [--json ... | --file ...]`. Raw clients put the token in argv, shell history and logs.
3. The token never appears in argv, command output, logs, commit messages, or chat. Do not `cat .env`. Do not echo `$IGNITION_API_TOKEN`.
4. A missing CLI capability is an SDK bug. If no verb or option expresses the shape needed, fix the Pydantic model or add the option in the `ignition-gen-sdk` repository (with a test), then run the CLI. Never hand-write JSON to fill the gap, and never call `ProjectDiskBackend` or the models from a one-off script to route around the CLI.
5. Disk writes need a scan. Every disk-writing verb scans by default; only pass `--no-scan` when the gateway is deliberately offline, and then tell the user a scan is still owed.

Full text with rationale: `references/hard-rules.md`.

## 7. Project layout the agent maintains

```
<project>/
  .env                              credentials (gitignored)
  .ign/                             SDK state: openapi.json, api_reference/, manifest/, client/, validate.png (gitignored)
  .ign_tools/                       the user's own generators; `ign tools list`, `ign tools run NAME [ARGS]`
  .agents/skills/ignition-local/    project-specific learnings the agent appends to
    SKILL.md
```

`.ign_tools/NAME.py` scripts import `ignition_gen_sdk` and run as `__main__` via `ign tools run NAME`. They are seeds for whole resource families and should import `ignition_gen_sdk.tools.seed_guard` so they refuse to overwrite views someone has since edited in the Designer.

`.agents/skills/ignition-local/SKILL.md` is where gateway-specific facts accumulate: provider names and their permission quirks, which backend is available, project names, naming conventions, gotchas discovered while working. The agent appends there; it never modifies the installed plugin skills. The `skill-learn` skill formalizes the append. Template in `references/project-layout.md`.

## Quick checklist

```
[ ] ign --help works (or python3 -m ignition_gen_sdk.cli)
[ ] .env present in cwd with IGNITION_URL + IGNITION_API_TOKEN (name:secret)
[ ] API key has a security level listed in Gateway Write Permissions; secure connections off if IGNITION_URL is http://
[ ] .env and .ign/ gitignored
[ ] ign api GET /data/api/v1/gateway-info answers (spec fetched to .ign/openapi.json)
[ ] ign provider names lists providers (client generated)
[ ] ign openapi docs rendered .ign/api_reference/
[ ] backend determined: disk (data dir visible) or API-only
[ ] .agents/skills/ignition-local/SKILL.md exists with the facts above
```

## References

| File | Summary |
|---|---|
| `references/env-contract.md` | Every environment variable, defaults, resolution order, token format check |
| `references/write-backends.md` | API vs data-dir backends, which verbs use which, `auto` fallback, scan endpoints |
| `references/hard-rules.md` | The five non-negotiable rules with the failure each one prevents |
| `references/project-layout.md` | `.ign/`, `.ign_tools/`, and the `ignition-local` skill template |
