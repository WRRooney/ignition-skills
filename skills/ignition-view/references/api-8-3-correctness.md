# 8.3 API correctness

Ignition 8.3 restructured much of the scripting and expression API. Code that
passes model validation can still throw at runtime because a function only ever
existed in 8.1, or never existed at all. Validate against the 8.3 catalog, not
memory and not 8.1-era sample projects.

## The catalog and the audit

```bash
ign builtins refresh                       # re-crawl docs.inductiveautomation.com into the package catalog
ign builtins audit --project Demo          # report system.* calls and expression functions absent in 8.3; exit 1 if any
ign builtins audit --allow cirruslink      # accept a module-provided namespace
```

The crawl covers the scripting index completely (every `system.*` function is
link-listed). Expression functions have a blind spot: inline-documented ones are
not link-listed, so to settle whether one exists probe its page,
`.../docs/8.3/appendix/expression-functions/<category>/<fn>`; 404 means absent.

The same catalog backs the author-time guards: `bind_expression` rejects unknown
expression functions; `add_event` and `ign script write` reject unknown
`system.*` calls. If a real function is flagged, add it to
`ignition_gen_sdk.validation.ignition_builtins` rather than weakening the guard.

## 8.1 to 8.3 renames that break copied code

| 8.1 | 8.3 |
|---|---|
| `system.db.runQuery`, `runScalarQuery`, `runUpdateQuery`, `runPrepQuery` | `system.db.execQuery`, `execScalar`, `execUpdate`, `execUpdateAsync` |
| `system.db.clearNamedQueryCache` | `system.db.clearQueryCache` |
| `system.date.addHours`, `addDays`, `secondsBetween`, `getYear`, ... | `system.date.add`, `dateArithmetic`, `dateDiff`, `dateExtract`, `get`; `now`, `toMillis`, `fromMillis` unchanged |
| `system.dataset.toDataSet` | `system.dataset.toDataset` (casing) |
| `system.net.http*` | `system.net.httpClient` |
| `system.gui.*`, `system.nav.*`, `system.print.*` | `system.vision.*` |
| `system.tag.browseTags` | `system.tag.browse(path, filter).getResults()` |
| `system.perspective.setSessionProperty` / `getSessionProperty` | never existed; `self.session.custom.*` in component scope |

New namespaces in 8.3 include `system.eventstream`, `system.historian`,
`system.kafka`, `system.secrets`. Installed modules add namespaces the core
docs do not list (an MQTT module's `system.cirruslink.*`); `ign builtins audit
--allow <ns>` admits them, and a whitelist must also accept namespaces harvested
from scripts already running on the gateway.

## Functions that do not exist in 8.3

- `system.perspective.getSessionProperty` / `setSessionProperty`. Access the
  session in component scope: `self.session.custom.<path> = v`. A project library
  function has no `self` and no session; keep it pure and do session I/O in the
  component's `onStartup` or action script. Declare the prop first with
  `ign session-props declare`.
- `system.tag.browseTags` (7.x). Use
  `system.tag.browse(path, {"tagType": "UdtInstance", "recursive": True}).getResults()`;
  each result is dict-like (`r["fullPath"]`, `r.get("typeId")`).
- `system.db.runQuery` / `runNamedQuery` shapes changed; check the 8.3 db page.
- Expression: `contains`, `join`, `length`, `substringAfterLast`, `startsWith`,
  `addDays`, `secondsBetween`, `randomInt` (see `expression-idioms.md`).

## Nested UDT typeId filters

`system.tag.browse` with `typeId: "Folder/Type"` (a type nested under a folder)
returns empty even when instances exist; a root-level type name works. Browse with
`{"tagType": "UdtInstance", "recursive": True}` only and post-filter on the leaf:
`str(r.get("typeId") or "").rsplit("/", 1)[-1] == "Type"`.
`system.tag.query` with a `hierarchy: [{"typeId": ..., "relationship": "SubType"}]`
condition does match nested types. Results are dict-like (`r["fullPath"]`,
`r["name"]`, `r.get("typeId")`, `r.get("dataType")`); a browse without a filter
returns direct children only.

Never swallow the browse: `except Exception: return []` turned a removed API
into an "empty navigation" mystery. Log with a named logger
(`system.util.getLogger("plant.nav")`), then `ign logs --search plant.nav`
after a real session shows the counts or the traceback.

## Java collections in Jython

A Java `Map` reaches Jython with a one-argument `get()`, so `.get(k, default)`
raises. Convert through `json.loads` or `dict(m)` first.

## Logic ported to CPython is not proof

A CPython test of ported logic cannot catch a Jython-only failure or a missing
8.3 function. Exercise the code from a Perspective view (or the Designer script
console) and read `ign logs --search <module> --min-level ERROR --stack`.
