# Hard rules

Each rule exists because breaking it once caused real damage on a live gateway.

## 1. The SDK is the sole writer of Ignition files

Files under `config/resources/**` and `projects/**` are created and changed only by `ign` verbs, which serialize from validated Pydantic models. Banned vectors, all of them: editor Write/Edit tools on those paths, shell redirection (`>`, `>>`, `tee`), `sed -i`, `cp`, `mv`, `rm`, and Python `json.dump` or `write_text` aimed at those paths.

Why: hand-written config hallucinates shapes the gateway rejects or, worse, accepts and misinterprets. A view whose `events` block lacked the `component` layer would not open; the file was valid JSON and the scan reported nothing. The model is the single source of truth: if a shape is not modeled, it is not written.

Deletion is included. `ign tag delete` and `ign view delete` are the sanctioned removers; `git checkout` and `git clean` on those paths are version-control operations and are fine, followed by a scan.

## 2. The CLI is the interface, not just the package

Calling `ProjectDiskBackend`, `DiskBackend` or a model from a one-off script to route around a missing CLI option is not acceptable even though it uses SDK code. It skips the CLI's validation, `--dry-run`, scan handling and manifest recording, and leaves the gap in place for the next agent.

A missing capability is an SDK bug: add the option or fix the model in the `ignition-gen-sdk` repository with a test, then run the CLI. The only sanctioned non-CLI callers are committed generators under `.ign_tools/`, run via `ign tools run`, which are reviewable seeds that use the same models.

## 3. No raw HTTP clients

`curl`, `wget`, `httpx`, `requests` and any ad-hoc HTTP call against the gateway are banned, including "just a quick check". They require the `X-Ignition-API-Token` header on the command line, which leaks the token into argv, shell history, hook logs and the transcript.

`ign api METHOD PATH [--json '...' | --file body.json] [--strict] [--confirm] [--dry-run]` covers every `/data/api/v1/*` endpoint through a long-lived client that owns the header. Non-GET methods prompt for confirmation when stdin is a terminal; pass `--confirm` in non-interactive runs. `--strict` needs the `[strict]` extra.

## 4. The token never leaves the environment

Never print `.env`, never echo `IGNITION_API_TOKEN`, never paste the token into a commit message, issue, or chat reply. If the user offers to paste it into chat, ask them to put it in `.env` instead.

## 5. Every disk write is followed by a scan

After any change under `projects/**`, `POST /data/api/v1/scan/projects`; after any change under `config/resources/**`, `POST /data/api/v1/scan/config`. All `ign` disk-writing verbs do this by default (`--scan`). Pass `--no-scan` only for offline work, and say so, because the gateway will not see the files until a scan or restart.

## Consequences when a rule is blocked by the host

Some hosts install a guard that rejects shell commands writing to protected paths. If a command is blocked, do not rephrase it to slip past the guard. Find the `ign` verb, or add one.
