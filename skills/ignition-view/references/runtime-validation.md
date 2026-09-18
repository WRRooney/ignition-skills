# Runtime validation with `ign view validate`

Model-valid is not rendered. Views that pass every structural check still fail at
runtime: an invalid icon path, a nonexistent 8.3 function in an `onStartup`, a
dead binding. The only proof is a render.

## Running it

```bash
ign page list --project Demo --json
ign view validate --project Demo                          # root page "/"
ign view validate --project Demo --page overview          # "/overview"
ign view validate --client-path /data/perspective/client/Demo/overview
ign view validate --url http://gateway:8088/data/perspective/client/Demo/overview --out /tmp/overview.png
```

Perspective renders mounted pages, not raw views, so mount a scratch page first
(`ign page mount --project Demo --url /probe --view-path Components/PumpFaceplate`),
validate, then `ign page unmount`. Mount in the project whose client renders it.
The base URL defaults to `IGNITION_URL` (env or `.env`); `--base` overrides it.
The screenshot defaults to `.ign/validate.png`; `--out` overrides it. No token is needed:
the Perspective client answers anonymously even when the gateway forces IdP login
for the Designer. A "Personal Use Only" EULA modal (Maker edition) is dismissed
automatically.

## What the verdict means

| Signal | DOM | Meaning | Exit |
|--------|-----|---------|------|
| `component_crashes` + `crashed_components` | `.component-error-boundary` | A component threw (a real bug; the `data-component` type is listed) | 1 |
| `view_state_messages` | `.ia_viewStateDisplay__primaryMessage` | "View Not Found" or "No view configured": the route or view path did not resolve | 1 |
| `http_status >= 400` | | | 1 |
| `quality_error_overlays` | `.ia_qualityOverlay--error` | Bound data has bad quality (a data signal, not necessarily a view defect) | 0, warning |
| `console_errors` | | Browser console errors, e.g. `React.cloneElement(null)` from a bad icon or empty embed path | 0, warning |
| `symbol_svg_empty` | empty hidden `ia.symbol.*` svg | The cold-session symbol race (`symbols.md`) | 0, warning |
| `login_wall` | | Password field plus sign-in text; check the screenshot | 0, warning |

A negative count means the detector itself errored and is treated as a failure.
Always read the screenshot (`--out`); the visible-text sample is a hint, not proof.

## Health sweep

`ign page list --project Demo --json`, then one `validate` per URL (root omits
`--page`; `/x` becomes `--page x`) and collect the verdicts.

## Blind spots

- **`onStartup` never completes headlessly.** The session connects and closes on
  browser exit before gateway-scope `onStartup` runs, so `view.custom.*` data set
  by `onStartup` (a nav tree, KPI tiles) stays empty. Components that need no
  startup script render fine. Verify startup-driven views in a real browser or the
  Designer.
- **The session is anonymous.** On a provider whose write permission requires
  authentication, tag reads work, bidirectional bindings toast
  `Error writing to Value: Bad_ReadOnly` on their initial write-back, and
  `system.tag.getConfiguration` returns nothing, so discovery-driven forms render
  headers with zero fields. Validate leaf views by embedding them with an explicit
  `tagPath` param; confirm discovery in an authenticated session.
- **Silent failures pass clean:** a view nested inside another view's directory,
  a dangling `{view.custom.x}` reference, a `==` in an expression, a binding on a
  prop the component does not have, a dict cell rendered as "null" (that one does
  raise a quality overlay).
- **Timing.** Symbol blanks and drag interactions are not reproducible headlessly.

## Requirements

The `runtime` extra (`uv tool install 'ignition-gen-sdk[runtime] @ git+https://github.com/WRRooney/ignition-gen-sdk'`, or
`pip install -e '.[runtime]'` from a checkout) and `playwright install chrome`
(uses the system Chrome channel). Exit 2 when absent. Core logic lives in
`ignition_gen_sdk.validation.runtime` (`validate`, `verdict`, `warnings`).
