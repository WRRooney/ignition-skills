# Why raw HTTP clients are banned for gateway calls

Every Ignition 8.3 API call needs the `X-Ignition-API-Token` header. A raw
client (curl, wget, httpx one-liner, requests script) has to receive that
header value as a command-line argument or an inline string, which leaks it
into:

- the process argument list (visible to `ps` and to any other user on the host)
- shell history
- hook and audit logs that record executed commands
- the agent's own tool output and transcript

`ign api` closes all four channels. It loads the token once through
pydantic-settings (process environment first, then `.env` in the current
directory), stores it only inside the httpx client's header dict, and scrubs
it from anything it prints. The `Settings` object's `repr` and `str` replace
the token with `[REDACTED]`.

## Rules for the agent

- Every `/data/api/v1/*` call, including trivial ones such as
  `/gateway-info` or `/scan/projects`, goes through `ign api METHOD PATH`.
- If `ign` is not on PATH, run `python3 -m ignition_gen_sdk.cli api ...`; do not
  fall back to curl "just to check".
- Never print, cat, or grep the `.env` file for the token.
- Never prefix a token-printing command with an inline-execution form that
  would splice its output into the prompt.

## Environment contract

```
IGNITION_URL        http://localhost:8088      (required)
IGNITION_API_TOKEN  <name>:<secret>            (required, the full header value)
IGNITION_DATA_DIR   /path/to/gateway/data      (only for disk-backed verbs)
IGNITION_STATE_DIR  ./.ign                     (optional)
```

`IGNITION_API_TOKEN` must contain the colon; a bare secret fails settings
validation with an `Auth error` before any request is made.
