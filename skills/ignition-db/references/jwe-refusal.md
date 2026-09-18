# The JWE refusal rule

Ignition encrypts stored credentials with AES-256-GCM and writes them as a
JOSE/JWE object. On disk a password looks like:

```json
"password": {
  "type": "...",
  "data": {
    "ciphertext": "...",
    "encrypted_key": "...",
    "iv": "...",
    "protected": "...",
    "tag": "..."
  }
}
```

The key material lives inside the gateway. Tooling cannot produce a valid
blob, and a copied blob from another gateway is unreadable on this one, so
any attempt to hand-write one produces a connection that silently fails to
authenticate.

## What the SDK does

- `ConnectionConfig.password` has a validator that refuses any value whose
  keys include all five of `ciphertext`, `encrypted_key`, `iv`, `protected`,
  `tag`, whether flat or nested under `{type, data}`. The error is raised
  before any HTTP request.
- `ign api` walks every request body recursively and rejects any nested
  object with the same five keys as a `Payload error`.
- HTTP binding models in views apply the same guard to their auth data.

The refusal message names the rule and tells you to set the value in the
Gateway web UI.

## Where the guard does not fire

`ign db-conn create/update --dry-run` prints the resolved payload and exits 0
before the model is built. A dry run therefore accepts a JWE-shaped password;
only the real call refuses it.

## How to set a real password

- Plaintext through the CLI: `--password-stdin` (piped, one line) or the
  hidden tty prompt. The gateway encrypts it on receipt.
- Any other secret (keystore passwords, OPC credentials, SMTP): the Gateway
  web UI.

Never copy a `password` object out of one `config.json` into another file.
