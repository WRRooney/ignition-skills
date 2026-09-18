# Environment contract

`ign` builds a `Settings` object on every invocation. Values resolve from the process environment first, then from a `.env` file in the current working directory. There is no global config file; run `ign` from the directory that holds `.env`.

| Variable | Default | Notes |
|---|---|---|
| `IGNITION_URL` | `http://localhost:8088` | Gateway base URL. Use the port reachable from the shell running `ign`. A container-internal hostname such as `ignition:8088` only resolves between containers on the same network. |
| `IGNITION_API_TOKEN` | none (required) | Full `X-Ignition-API-Token` header value, `<name>:<secret>`. `ign` validates the shape and fails with `IGNITION_API_TOKEN must be the full header value '<name>:<secret>'` otherwise. |
| `IGNITION_DATA_DIR` | `.` | The gateway data directory: the one containing `config/resources/` and `projects/`. Only needed for disk-backend verbs. |
| `IGNITION_PROJECT` | `Global` | Default `--project` for Perspective verbs. |
| `IGNITION_TAG_PROVIDER` | `default` | Default `--provider` for tag verbs. |
| `IGNITION_OPC_SERVER` | `Ignition OPC UA Server` | Default `opcServer` for OPC tags built through the library. |
| `IGNITION_STATE_DIR` | `.ign` | SDK state directory. |
| `IGNITION_OPENAPI_SPEC_PATH` | `<state>/openapi.json` | Override for the fetched spec location. |
| `IGNITION_OPENAPI_GENERATED_CLIENT_PATH` | `<state>/client` | Override for the generated client. |
| `IGNITION_OPENAPI_HASH_SIDECAR_PATH` | `<state>/openapi.hash` | Override for the spec hash sidecar. |

Lower-case forms (`ignition_url`, `ignition_api_token`, ...) are accepted as aliases.

## State directory layout

```
.ign/
  openapi.json        gateway spec; fetched on first use, refreshed by ign openapi fetch
  openapi.hash        spec hash used to skip regeneration
  client/             typed client generated on first typed verb (ign openapi gen --force regenerates)
  api_reference/      INDEX.md, AUTH.md, one markdown file per endpoint group (ign openapi docs)
  manifest/           last-pushed payload hashes (ign diff)
  validate.png        default screenshot path of ign view validate
```

Everything in `.ign/` is regenerable. Gitignore it together with `.env`.

## Token handling

- `Settings.__repr__` prints `api_key=[REDACTED]`; the token is never formatted into error messages.
- `ign api` output passes through a scrub that masks any `name:secret`-shaped string.
- Missing or malformed credentials surface as `Auth error` with the hint `Check IGNITION_API_TOKEN (env or .env)`. The underlying validation message is deliberately not printed, so the token value cannot leak through an exception.

## Checking the environment without leaking it

```bash
test -f .env && echo ".env present"
grep -c '^IGNITION_API_TOKEN=' .env       # 1 means set; never print the line itself
ign provider names                         # proves URL + token together
```
