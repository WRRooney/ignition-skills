# Lessons: implementation strategies behind the skills

This file records the implementation strategies and best practices the skills in this repository are built on. It is for
contributors. The skills themselves stay short and point here, or to a reference file, when a rule needs its reasoning
spelled out.

The lessons were mined from a long findings log produced while an agent built Perspective views, tags, UDTs, scripts,
alarm screens, and a reusable Perspective framework on a live Ignition 8.3 gateway through the `ign` CLI (package
`ignition_gen_sdk`), then checked the result against the gateway itself. Each lesson is a bold one-line rule followed by the
failure it prevents and when it applies. Duplicates in the log were merged. Nothing here depends on a particular
project; example names are `Demo` (template project), `Site1` (child project), `default` (provider), `Tanks/T01` and
`Area1/Pump01` (tags), `Pump`, `Valve`, `Tank` (UDT types), and `Components/PumpFaceplate` (view).

Where a lesson has a matching reference file in a skill, the skill's `references/` directory is named so the two stay in
step.

## 1. Model the gateway's wire shape, not the Designer's UI

**Ground truth is a file the gateway wrote, never a memory of the Designer.** Every shape bug in the log came from
guessing what a view, tag, or resource looks like from the Designer's property panel. The only reliable references are
Designer exports, the on-disk `projects/**` and `config/resources/**` trees, and `/tags/export`. Before modeling a new
shape, find at least one gateway-written sample and diff against it byte for byte.

**Component events live under a category layer: `events.component.<name>`.** A view whose events dict is flat
(`events.onActionPerformed`) validates as JSON and silently will not open. The handler is one flat object `{type, scope,
config}`, not a list; categories are `component` and `dom`. Handler types seen in exports are `script`, `nav`, and
`popup`; an unmodeled handler type rejects the whole view on load, so tooling must accept all three (ignition-view
`model-shapes.md`).

**View params are bare scalars; binding type is `"property"`, not `"prop"`.** Agents borrow the UDT parameter shape
`{value, dataType}` for view params and abbreviate the binding type. Both pass schema-only validation and both fail at
runtime. Reject the `{value, dataType}` fingerprint in the params validator and make the binding type a discriminated
literal.

**A constant is a plain prop value, never a binding.** Wrapping a static string (a style class, a title) in an
expression binding is what the gateway's own exports never do, costs an evaluator per component, and reads as an error
to reviewers. If an expression contains no `{` and no `(`, it is a constant; set the prop directly.

**Indirect tag bindings use placeholders plus a `references` map.** The wire form is `tagPath: "{1}/Status/Running"`
with `references: {"1": "{view.params.tagPath}"}`; named keys work too. A bare `{tagPath}` token with no matching
reference, or an inline `{view.params.x}` in the path, looks plausible, validates, and resolves to bad quality on every
bound prop. Put the provider-qualified path in the param value, not in the template.

**Transforms nest under the binding, not beside it.** `binding.transforms[]` holds `{type: map|format|script|expression,
...}`; a misplaced sibling `transforms` array is ignored without error and the prop shows the untransformed value. The
format key is `formatValue`, never `pattern`; polling `rate` and `numRows` are strings. A query binding references a
named query by `queryPath` and passes `parameters`, never raw SQL.

**Container children carry a typed `position` that differs per container.** Flex uses `{basis, shrink, grow, display}`,
split `{position: left|right| top|bottom}`, tab `{tabIndex}`, breakpoint `{size: small|large}`, column `{breakpoints:
[{colIndex, name, order, rowIndex, span}]}`, coordinate `{x, y, width, height, rotate: {anchor}}`. Tab children are a
flat list keyed by `tabIndex`, not nested under a tab. The breakpoint container's type string is `ia.container.breakpt`
(ignition-view `container-positions.md`).

**Do not over-constrain on thin evidence.** Column breakpoint names are `sm/md/lg` in every sample, but the gateway
accepts custom names, so a `Literal` would reject valid views. When a corpus shows one value set but the platform
documents freedom, type it as `str` and validate keys, not values. The same applies to `rotate` (only `anchor` observed;
`angle` exists).

**Component type strings and prop names must be copied, not derived.** The numeric input is
`ia.input.numeric-entry-field`; the text placeholder prop is `placeholder`; the radio group takes `radios`, not
`options`. Never build a type string or prop name from a display name; take it from a sample or from `ign component
list`.

**Unknown component props are silently kept and ignored.** Perspective does not reject a prop it does not know, so a
snake_case guess (`read_only` for `readOnly`, `align_vertical` for `alignVertical`) lands as a junk key and the real
prop stays unset. A generator that lets extra props through for forward compatibility must flag any underscore key whose
camelCase twin is a known field.

**`resource.json` must list only files that exist.** A view manifest that names `thumbnail.png` when no thumbnail was
written makes the gateway log a `NoSuchFileException` on every scan, forever, and the running gateway keeps expecting
the file even after the manifest is fixed on disk (a restart clears it). List `["view.json"]` and let the Designer add
the thumbnail.

**Never try to compute `lastModificationSignature`.** It is a gateway-side digest that does not derive from the resource
content in any reproducible way, and its absence is not a load gate: unsigned resources load fine. Omit it, preserve an
existing block untouched, and exclude `attributes` when hashing a resource for change detection.

**Match the Designer's emit policy or accept churn on every save.** Keys ASCII-sorted (`udts.json` forces `tags` last),
UDT member and instance arrays name-sorted, `> = & '` escaped Gson-style, non-ASCII written literally, whole-number
history props emitted as ints. Explicit `null` for `position.basis/grow/shrink` and Perspective defaults (`direction:
"row"`, `basis: "auto"`, `grow: 0`, `params: {}`, `overflow: "auto"`) are churn; do not emit them.

**Tag data type names on the wire are `Float8`/`Float4`, not `Double`/`Float`.** An enum whose labels say `DOUBLE` and
`FLOAT` must serialize to `Float8` and `Float4`; `Integer` and `Int4` are accepted aliases. A memory tag pushed with
`value` comes back with both `value` and `defaultValue`.

## 2. Verify against runtime, not against memory

**"Validates through the model" is not "renders on the gateway".** The single most repeated lesson. Views that passed
schema validation, structural audits, and hundreds of unit tests crashed every embedded symbol on first render (invalid
icon path) and showed an empty navigation tree (dead scripting API). Schema validation catches shape; only a render or a
gateway log catches behavior. Budget for a render step in every view task.

**A Python port of a Jython script cannot find Jython bugs.** Tests that re-implement a script's logic in CPython over
fixture data pass while the real script throws on `system.tag.browseTags` (removed) or a nonexistent
`system.perspective.setSessionProperty`. Ports are also blind to the target expression language (they accept `==`). If
you must test headlessly, `exec` the real `code.py` with a fake `system` module injected, so the source under test is
the shipped source.

**Library scripts are testable from CPython when they stay portable.** Keep modules ASCII (a `# -*- coding -*-` cookie
is a `SyntaxError` because project scripts compile from a unicode string), tab-indented consistently (Jython tolerates
mixed tabs and spaces; Python 3 refuses), and free of `system.*` calls in pure logic. Load the module by path and mock
the `system` surface.

**Moving a resource moves its tests.** Fixtures that load a live project script by path error at setup, which reads as a
green suite unless the error count is checked. Expect zero errors, not zero failures.

**Render headlessly, and read the right DOM signals.** A Perspective client URL renders without a login wall, so a
headless browser can screenshot any mounted page. `.component-error-boundary` means a component crashed (a view defect);
`.ia_qualityOverlay--error` means bound data has bad quality (a data signal, not necessarily a view defect). Report the
two separately and let only crashes fail the check (ignition-view `runtime-validation.md`).

**A detector that errors must fail, not pass.** A validation verdict that treated "could not count crashes" (a `-1`) as
"zero crashes" reported a broken view as clean. Any inconclusive probe result is a failure with an "inconclusive"
reason.

**View `onStartup` does not fire in a short headless session.** Anything a view populates from `onStartup` (a nav tree,
KPI tiles) stays empty under headless rendering even when the session reports connected. Do not read that emptiness as a
bug; verify `onStartup`-driven views in a real browser or Designer session, and give the script a self-confirming
`logger.info` so the gateway log proves it ran.

**The gateway log is the first diagnostic, not the last.** `ign logs --search <term> --min-level ERROR --stack` returns
Jython tracebacks, including `Could not initialize project script module '<pkg.mod>'`. Forty rounds of guessing at a
reload theory were replaced by one log query. Check the log immediately after any write that changes a script, and
filter by logger name. Log entries persist: an old error is not a current error (ignition-api `gateway-logs.md`).

**Read a live tag value with a probe view, not with the API.** There is no REST tag read; `/tags/export` returns
configuration only. To learn whether a tag resolves with good quality, mount a scratch view with a direct binding to it,
render headlessly, and remove the view afterward. A probe view whose transform calls a library function inside
`try/except` and logs `traceback.format_exc()` diagnoses silent module failures the same way.

**Build a real, end-to-end example before declaring a framework done.** Three clean structural audits missed a call to a
function defined in a different module; the first real project built on the framework exposed it in one pass. Generated
view families, scripts, and UDTs should be exercised by one throwaway project that uses them the way a user would.

**Test the documentation with a fresh agent that has no context.** Spawn an agent whose only input is the skill or
README and a dry-run task. Where it reads source code to succeed, the doc has a gap; where it guesses wrong, the tool
needs a guard. This found missing import paths, undocumented kwargs, and a crash-on-typed-props helper, none of which
the author noticed.

**A one-shot audit becomes a regression test the same day.** Every manual sweep in the log (no static bindings, no `==`,
no dead API, every alarm key modeled, every position key modeled) was later re-broken until it was locked as a test over
the on-disk corpus. Write the audit as a test that skips when the corpus is absent.

**Grep JSON with a parser, not a regex.** A search for `"Critical"` missed the escaped `\"Critical\"` inside a binding
expression and reported the stale expression gone. Load `view.json` and walk it.

**Prefer measurable checks over reviews when the ground truth is a file.** Byte-identical round trips against Designer
exports settled every shape argument in the log faster than any discussion.

## 3. Bindings, expressions, and transforms

**Ignition expression equality is a single `=`; `==` is a silent parse error.** The binding never evaluates and the prop
keeps its default, so an alarm color that "never resolves" is often this. `!=`, `&&`, and `||` are valid. A generator
should reject `==` outside quoted literals at author time (ignition-view `expression-idioms.md`).

**Expression function names are case-insensitive; `system.*` calls are not.** Real exports contain `COALESCE`, `isnull`,
and `tostr`. A checker that compares expression names case-sensitively rejects valid work; a checker that folds case for
Jython calls accepts a typo the gateway will throw on.

**Unbalanced `()` or `{}` fails silently, like `==`.** Add a running-depth check over the literal-stripped expression to
any expression entry point, so a `)` inside a string does not count.

**Guard every expression entry point, or none of them count.** The `==` guard lived only on the component binding
helper; the expression transform, the view-level custom expression, and a hand-built `propConfig` dict all bypassed it.
Route every raw expression string through one validator, and forbid hand-assembled binding dicts in build scripts.

**Prefer the cheapest binding tier that expresses the value.** Property binding, then expression, then script transform,
then event script. `runScript()` in an expression is script-tier cost: it runs Jython on every evaluation. It is
legitimate for load-time config reads with poll rate 0 and wrong for anything that tracks a process value.

**`view.custom.*` is the only data surface components bind to.** Never call `tag()` in an expression. Tag-bind a custom
prop once, then property-bind components to it: one place to change the tag path, one place to inspect quality, and the
component tree stays reusable across instances. Data goes on `custom`; presentation stays on the component.

**Compute a state string once, fan it out with property bindings.** When one state drives several components, compute
the class string on a view custom prop and property-bind every consumer to it. Property bindings are the cheapest tier
and the state vocabulary has one edit site.

**Bidirectional custom props are the write channel.** Event scripts assign `self.view.custom.foo`; the bidirectional tag
binding performs the write. For multi-value commands, bind a dict prop plus a trigger bool. No `writeBlocking` for one
or two tags. Bidirectional bindings write back once on mount, which shows as a `Bad_ReadOnly` toast in an anonymous
session on a protected provider.

**Bad-quality guards wherever a boolean drives UI.** `if(isGood({value}), {value}, false)` keeps anonymous or offline
sessions from painting "null". `coalesce({value}, 0) >= 75` for numeric compares. Hidden on failure is the exception,
chosen deliberately to avoid pop-in, and documented where it is used.

**Cross-view navigation inside an embedded view needs a session prop.** An embedded view cannot write its parent's
`view.custom.*`, and `system.perspective.navigate` moves the whole page, not an embedded view's `props.path`. Declare a
session prop, write it from the nested click, and bind the container's embed to it (ignition-view
`session-props-and-messaging.md`).

**Expression bindings do not run inside event scripts.** A click handler that needs a computed target must read the
value from a prop the expression already populated, or compute it in Python.

**Expression-structure bindings fire on null members.** `expr-struct` with `waitOnAll: true` still runs its transform
when a member resolves to `null`; test each member with `is None` in the script. Use them to hand several scalars into
one script transform and return a keyed object.

**Guard every discovery transform against a null or empty path.** Bindings fire on first mount with `null`; `waitOnAll`
does not hold a script transform back. An empty path handed to `getConfiguration` or a `/*` query is the whole provider,
recursively, plus a blocking read per field. The first line of every transform that feeds a browse is `if value is None
or value == '': return []` (ignition-view `discovery-transform-null-guard.md`).

**Gate `props.path`, not `position.display`, on embeds.** A hidden `ia.display.view` stays mounted and its bindings keep
running. Bind `props.path` to `''` to defer loading; an empty path renders nothing but logs a `React.cloneElement(null)`
console error, so a repeater with zero instances is the cleanest optional embed.

**Enum params: lowercase once, then map.** Every consumer is `lower({view.params.x})` mirrored into a custom prop,
feeding a map transform with a `fallback`, never a nested `if()` chain. Every `{view.custom.<name>}` referenced in an
expression must exist as a key in the view's `custom` block; a dangling reference resolves falsy with no error.

## 4. Scripting: 8.3 APIs and where agents hallucinate

**8.3 is not 8.1, and the shipped sample projects are 8.1-authored.** More than a hundred `system.*` functions were
removed or renamed between the versions. Validate every call against the 8.3 documentation, not against memory or
against sample project code (ignition-view `api-8-3-correctness.md`).

**The APIs agents invent most often.** `system.perspective.setSessionProperty` and `getSessionProperty` (do not exist;
use `self.session.custom.*` in component scope), `system.tag.browseTags` (removed; use `system.tag.browse`),
`system.date.addHours` and friends (consolidated), `system.db.runQuery` (renamed `execQuery`), and the expression
functions `contains`, `join`, `length`, `substringAfterLast` (use `indexOf(...) >= 0`, a script, `len`, and
`substring(s, lastIndexOf(s, "/") + 1)`). Also `/tags/read`, `/tags/browse`, and `/tags/write` REST endpoints: only
`/tags/export` and `/tags/import` exist. There is no random function in the expression language.

**A function-name whitelist must be sourced, then hardened against a corpus.** A whitelist built partly from the
framework's own usage whitelisted the framework's own hallucinations. Source it from the documentation, union it with
names the gateway already accepted on disk, then run it over every real project on the gateway to find false positives
before enforcing it. Enforce subpackage names everywhere and leaf names only where the list is complete.

**Documentation crawls have blind spots; per-function pages are authoritative.** A category-page crawl of expression
functions returned the same count for 8.1 and 8.3 because inline-documented functions are not link-listed. Probing each
function's own page (404 versus 200) settled it.

**Third-party module namespaces are not in the core docs.** A gateway-wide scan flags `system.cirruslink.*` or any other
module namespace as unknown. Harvest installed module namespaces from on-disk usage and tolerate them.

**Never bare-`except` around a `system.*` call in a library function.** Every empty-result mystery in the log was an
exception swallowed by `except Exception: return []`. Log the exception with a named logger, then return with the error
visible.

**Library scripts have no session; keep them pure.** A project library function cannot reach `self.session`. Have it
return data and let the component script (which does have `self`) do the session or view writes. This also makes the
library testable with a fake `system`.

**Logger and error conventions on every gateway routine.** Route gateway logging through `system.util.getLogger` with a
dotted, prefixed name (`App.Config.Nav`), catch everything, log the traceback, and surface failures in a status tag
rather than letting them escape a binding transform.

**The `typeId` browse filter does not match a nested UDT type's full path.** Browsing with `{tagType: "UdtInstance",
typeId: "Base/Pump"}` returns nothing for a type defined under a folder, while it works for a root-level type. Browse
with `{tagType: "UdtInstance", recursive: True}` and post-filter on the leaf of `result.get("typeId")`, or use
`system.tag.query` with a `SubType` hierarchy condition, which does match nested types.

**One recursive `system.tag.query`, any depth, then post-filter.** A condition `path: "<root>/*"` compiles to a
case-insensitive regex that crosses `/`, so one query reaches every level; adding `system.tag.browse` recursion is dead
code. It is a contains match, not a prefix match, so always post-filter `fullPath.startswith(root + "/")` (ignition-tag
`tag-query-wildcards.md`).

**Jython is 2.7 and Designer edits insert tabs.** No f-strings, no type hints. Indent with tabs; a space-indented module
becomes mixed-indent `IndentationError` on the first in-Designer edit. `ast.parse` under CPython 3 is a useful syntax
proxy but not a Jython guarantee.

**Java collections reach Jython with Java semantics.** A Java `Map` has a one-argument `get()`, so `.get(k, default)`
raises; a dataset cell holding a dict reaches a subview as its Python `repr`. Go through `json.dumps` and `json.loads`
at the boundary.

**Alarm status and journal queries are Jython-only.** There is no REST endpoint for `queryStatus` or `queryJournal`; the
resources API only configures the journal. Verify accrual by reading the journal database directly.

**User-management calls report failure in return values, not exceptions.** `system.user.addUser`, `editUser`, and
`removeUser` return a `UIResponse`; a rejected save looks like success unless its errors are read. The gateway's
`allowUserAdmin: false` governs only the web UI, not `system.user.*` writes.

## 5. Tags and UDTs

**Every atomic member of a UDT type needs `valueSource`, not just `dataType`.** Omitting it fails validation at author
time in a typed model and reads bad quality on the gateway if it slips through. Folder members carry neither.

**UDT types inherit through `typeId`; overrides carry only changed keys.** A child type does not repeat the parent's
members; a member override in a derived type carries just the keys that differ (for example `dataType` alone). A member
with no parent supplying it still needs `dataType` and `valueSource` (ignition-tag `udt-member-inheritance.md`).

**A UDT instance cannot add ad-hoc children to a type folder.** Setpoints, status bits, and any member the faceplate
will browse must be declared on the type (a child type is fine); instances only override values.

**Instance overrides fail silently in three ways.** An override leaf must restate `valueSource` or it reads bad quality;
an `alarms` override replaces the whole alarm so omitted keys take Ignition defaults, not the type's; an undriven alarm
bit at bad quality counts as active. The diagnostic is a folder whose `Alarm Metrics.ActiveUnackCount` equals the number
of alarms beneath it (ignition-tag `udt-instance-overrides.md`).

**UDT parameters are typed `{dataType, value}` dicts and are template-level.** They are bindable as `{paramName}` inside
member paths and are the right place for per-type metadata such as engineering units. Never leave a member bound to an
undeclared parameter; it can wedge the type so instances export as `tagType: Unknown` with no members.

**Type definitions and instances have different sidecar files and paths.** Types live under
`ignition/tag-type-definition/<provider>/<path>/udts.json`, instances under `ignition/tag-definition/...`. Intermediate
folders under `tag-type-definition` need their own `unary-resource.json` or the type hierarchy does not resolve. In an
export, types appear under a synthetic `_types_/` folder, and there is no per-resource REST read for them (ignition-tag
`tag-disk-layout.md`).

**The config scan merges member additions but refuses kind changes silently.** Turning an `AtomicTag` member into a
`UdtInstance` member leaves the gateway running the old shape with nothing logged. Delete the type, rescan, rewrite.
Whole-file type writes drop siblings; patch verbs exist for one property (ignition-tag `udt-scan-merge-semantics.md`).

**The alarm model must cover the whole corpus before it enforces `extra="forbid"`.** Modes like `AboveValue`,
`BelowValue`, `WhenTrue`, `OutsideValues` and priorities `Diagnostic` through `Critical` are the common set; a strict
model that misses one key rejects a real alarm at author time. Audit against every alarm on disk and lock it with a
test.

**A `tags/import` body is `{"tags": [...]}`, with provider and policy as query parameters.** The gateway rejects a bare
array (the CLI wraps one for you); `provider` in the body is ignored. Embedding a full folder hierarchy in the body
*and* passing `path=` creates `<Folder>_duplicate_N` litter; use one or the other. Default the collision policy to
`Overwrite`.

**A secured provider blocks the tag import API, not disk writes.** When `editPermissions` require the `Authenticated`
security level, `/tags/import` fails with `Insufficient Tag Provider Edit Permissions`; write that provider's tags to
disk and scan. Anonymous sessions can read but writes toast `Bad_ReadOnly`, and `system.tag.getConfiguration` returns
nothing there, so tag-driven discovery is empty in an unauthenticated session.

**Join tags and views through one flat, prefixed custom-property contract.** Put every UI-relevant knob on the tag node
as a flat custom property with a common prefix (`ui_view`, `ui_order`, `ui_label`) rather than as UDT parameters. Views
read them with indirect tag bindings (`{tagPath}.ui_label`), scripts with `system.tag.query` `returnProperties`.
Parameters still exist where member tags need `{Name}` substitution.

**Declare self-described ancestry for discovery.** A custom property like `ui_typeAncestors = "Field/_Field"` on base
types lets one `system.tag.query` plus a `startswith` post-filter find every instance of a family regardless of concrete
type. Abstract bases start with `_` and discovery skips any `typeId` containing `/_`.

**Opt-in members ship disabled; instances flip them on.** A type carries every optional knob with `enabled: false`; an
instance enables what it needs. The tag config property `.enabled` (dot-addressed) decides whether a field exists in the
UI; a member tag `/Enabled` (slash-addressed, process-driven) decides whether a rendered input is editable. Do not
conflate them.

**Negative order hides; positive order sorts.** An ordering property with bands (sections 5, displays 10, inputs 20)
sorts within a column; a negative value keeps the field configured but off the form. Custom numeric properties read back
as floats (`1.0`); coerce before `range()`.

**Config overrides must set both `value` and `defaultValue`** on a memory member, or the tag initializes from the type
default and the override silently does nothing.

**Expression tags driven by `now(1000)` make a self-firing alarm test bed.** `getSecond(now(1000))` yields a 0..59
sawtooth; alarms set across it raise and clear on their own, giving every priority and a chattering case without any PLC
(ignition-tag `alarm-test-bed.md`).

## 6. Project resources, registration, and inheritance

**A project scan loads everything: views, pages, tags, and library scripts.** A long detour assumed library `code.py`
needed a restart. It does not (for Perspective scope). If a change does not show after `/scan/projects`, the resource is
malformed or a runtime error is in the log; look there, do not reach for a restart (ignition-disk `scan-endpoints.md`).

**Config resources register live through the resources API; project resources need disk plus scan.** Database
connections, alarm journals, and tag providers created via `POST /data/api/v1/resources/ignition/<type>` (array body)
are live at once. Views, scripts, page-config, and session-props are written to `projects/**` and picked up by
`/scan/projects`; tags under `config/resources/**` by `/scan/config`.

**Take the config scan lock around disk writes.** `POST /scan-lock/config` before writing resources and let the trailing
scan release it; only take it when a scan will follow, otherwise it sits for the full hold and the gateway may read a
half-written file under its internal abort collision policy.

**`PUT /projects/{name}` replaces the whole project record.** A partial body resets every omitted field: `title` and
`description` go blank, `inheritable` flips to false, `parent` becomes empty. A child with `parent: ""` inherits
nothing, so every view and script from the parent vanishes at runtime. Send the complete record or restore from version
control (ignition-api `put-projects-full-replace.md`).

**Create projects with `POST /projects`, never by scaffolding `project.json`.** A disk-only project skips `global-props`
initialization and every later `PUT` that touches collection-stored fields fails. Set `defaultDb` and `tagProvider` in
the create call.

**One inheritable template project, one runnable child per site.** `Demo` holds views, library scripts, page config,
session props, style classes, stylesheet, and alarm pipelines with `inheritable: true`. `Site1` sets `parent: Demo`,
owns only site-specific views, and runs the sessions. Every site upgrades by pulling the template.

**Page-config and session-props inherit per resource, not per entry.** A child holding its own (even empty)
`page-config/` directory shadows the parent's routes completely, and no scan fixes it. The Designer saves a page-config
copy into whichever project is open, so check for an owned copy after any Designer session in a child and delete it.
Mounting a route into a child that has no page config recreates the resource with only the new route. A parent route may
name a view only the child defines; resolution happens at runtime in the child's scope (ignition-disk
`resource-inheritance-and-reload.md`).

**Session props are schema-declared, not created at runtime.** Custom session props live in `session-props/props.json`
as `{custom: {...}, propConfig: {}, props: {}}`; a script writing `self.session.custom.x` to an undeclared prop has
nothing to write to. Declare once in the inheritable parent, and again in any child that owns its own session-props
resource.

**A project script package is a folder with no `resource.json`.** Giving the package folder a `resource.json` makes the
gateway treat it as one empty script and hide every module beneath it. Module leaves are `<mod>/{code.py,
resource.json}` with `scope: "A"` and `attributes.hintScope: 2`; without `hintScope` the module is silently skipped.

**Library scripts hot-reload for Perspective scope only.** Gateway-scope callers (tag event scripts, timers, alarm
pipelines) keep the old module until a gateway restart, so a tag-to-tag probe of edited library code is trustworthy only
on the first run after a restart. Verify edited library code from a Perspective view.

**A gateway restart is one REST call, and "no pending restart" is not "no restart needed".** `POST
/data/api/v1/restart-tasks/restart?confirm=true` restarts the gateway; `GET /restart-tasks/pending` only tracks changes
made through the web UI, so disk-and-scan changes never enqueue anything. Restart only for stale in-memory state (a
removed manifest entry the gateway still expects, a gateway-scope script), and only with the operator's consent
(ignition-api `gateway-restart.md`).

**Collection GETs on some resource types return 405.** `GET /resources/ignition/tag-provider` is POST/PUT only; read
names via `/resources/names/ignition/<type>` or the CLI's list verb. Project style classes and views have no read-back
endpoint at all; verify them by disk shape and a clean scan.

**Never write to the `local` config layer for portable settings.** It is instance-specific and not synced to redundant
peers; `core` is the layer.

## 7. Framework architecture for reusable Perspective projects

**Route by literal view path stored on the tag, not by lookup table.** A custom property such as `ui_view =
"Field/Input/Dropdown"` is the entire routing mechanism: a generic wrapper view embeds `ia.display.view` with
`props.path` bound to `{tagPath}.ui_view`. Adding a new field type means one new leaf view and one new UDT type; no code
changes.

**Give every family exactly one choke point.** When many instances route through one wrapper, that wrapper is where
global per-item behavior lives: visibility gates, access control, tab titles. Anything added there applies everywhere at
once. Never re-implement a global rule in individual leaves.

**Self-binding composites take a single `tagPath`.** A rich component view (a bar, a tile, a popup) declares one
`tagPath` param and binds its own data internally. Parameter fan-in (fifteen scalar params) is reserved for generic
contracts such as table-cell subviews and layout flags. Embeds become one-liners and every instance of the same UDT type
renders the same way.

**Ship the framework as a domain vocabulary, not as code.** Config, descriptions, operator notes, and group ordering
live in Designer-editable data (view `custom` objects, tag properties). Library scripts discover and derive; they never
hold copy or lookup tables. Adding a card, a group, or a page is a Designer edit (ignition-view `params-and-config.md`).

**A folder anchor instance means "render this folder".** Dropping an instance of a section type into a folder turns that
folder into a form section with its own header, layout, and column config carried as custom properties on the anchor.
Component UDTs compose this: a `Pump` type holds a `Control` folder with an anchor, so the pump's control tab is an
embed of the generic section renderer pointed at `{tagPath}/Control`.

**Cache structure, read values live.** A navigation or discovery cache holds only what is expensive to derive (paths,
parents, depth, order, permissions). Labels, icons, view paths, and overrides come from indirect tag bindings at render
time so a Designer edit shows immediately. Stamp the cache with a version number and treat an older cache as a miss.

**Split search into an index binding and a filter binding.** The index pays the one blocking read over the tree and is
bound on the root alone; the filter is pure string work bound on the query. Bound together, every keystroke re-reads
every node.

**Directory access sits behind a swappable backend.** User management views never receive platform user objects; one
library dict of overridable operations (`listUsers`, `saveUser`, ...) is the seam for LDAP or REST directories, and
every mutation returns `{ok, message}`.

## 8. Navigation and security

**The URL is the state.** Two mounts cover every destination: a landing page and `/App/:relativeTagPath`. The nav node
is a tag; the whole relative path travels as one percent-encoded segment (`%2F` for `/`) because 8.3 has no catch-all
page param and rejects extra segments. Encode with `urllib.quote(s, safe='')`, never `urlEncode()`, whose `+` for space
survives decoding and corrupts labels (ignition-view `page-routing-and-docks.md`).

**Navigation points are tags.** An instance of a nav-node type dropped in a folder makes that folder a destination; its
label defaults to the parent folder name so the folder name is both label and URL segment. Adding a page is adding a
node tag, never a page-config mount. Only tooling pages get static routes.

**Every navigation goes through one `go()` function.** Crumbs, chips, palettes, flags, and header icons all call the
same library function so per-node redirect overrides and security gates apply everywhere without each caller knowing.
Well-known destinations resolve from config tags, not hardcoded paths.

**Enforce read security in one seam and fail closed.** Nodes may carry the standard tag `readPermissions` shape. Cache
each node's own and effective (ancestor-inclusive) requirement, filter every list through one function that calls
`system.perspective.isAuthorized`, and gate the router's `props.path` on a tri-state prop (`-1` checking, `0` denied,
`1` allowed) that mounts nothing until decided. Malformed or unverifiable requirements deny.

**Each form factor resolves its view independently.** Desktop, tablet, and mobile each read their own property, then a
path-derived candidate confirmed against `system.perspective.getProjectInfo()["views"]` (which includes inherited
views), then a shared default card grid. Never let mobile inherit the desktop view. A breakpoint container beats CSS
hiding here: the non-matching branch never mounts, so desktop repeaters do not evaluate at phone width.

**Breadcrumbs stop at the parent; a peer bar shows the current level.** The trail is ancestors only; siblings of the
current location render as chips with the current one highlighted. The bar is populated on every page so the header
never shifts.

**Hand off data by URL first, docked-view relay second, session props never.** When the payload must not pollute the
URL, store it in the docked header's own `view.custom`, navigate, and have the destination request it with a page-scoped
message on startup; the header replies and clears in one handler. Page-scoped messages do not queue for unmounted views,
so request/reply is mandatory. One-shot `session.custom` seeds are unbookmarkable and wrong across tabs.

**Selection flows up by message, and transient state is non-persistent.** A row cannot write its parent's props across a
view boundary; it sends a page-scoped message and the parent's root component handles it into an unbound `custom` prop.
That prop must be `persistent: false` or the Designer saves a preview-mode value as the mount seed.

## 9. Alarms, journals, and databases

**An alarm journal at `minPriority: Diagnostic` captures everything.** The default threshold drops diagnostic-priority
events, which is exactly what a KPI screen wants to count. The journal table `alarm_events` stores `priority` 0..4,
`eventtype` 0 active / 1 clear / 2 ack, and `eventtime` as epoch milliseconds in a text column (ignition-db
`alarm-journal-sql.md`).

**Index the journal before analyzing it.** `alarm_events` has primary key `(id, eventtime)`, so range predicates on
`eventtime` alone cannot use it. Add explicit indexes on `(eventtime)` and `(eventid)` before building analysis pages,
and fail loudly on SQL errors instead of falling back to `queryJournal`, which reads the same datasource and only hides
the fault.

**Bind alarm counts from Alarm Metrics tag properties, not `queryStatus`.** `{folder}/Alarm Metrics.ActiveUnackCount`
(dot-addressed) is a live tag property; the slash form is bad quality. There is no plain active count; sum the ack and
unack counts, and drive color off per-priority counts because `Highest*Priority` is null when nothing is active
(ignition-tag `alarm-metrics.md`).

**"Faulted" equals "any active alarm on the instance".** Bind `{tagPath}/Alarm Metrics.highestActivePriority` with
`isGood({value}) && !isNull({value})` and use the same signal for the tile frame and the symbol fault state.

**Alarm bindings live on the page, never on session props.** A session-scoped query binding polls in every open session
forever. Session props hold only the scope and range the user chose.

**Snap query windows to the poll quantum so the gateway cache hits.** Round the range end down to the polling interval
so every session sends identical parameters. Sniff the SQL dialect once from `system.db.getConnectionInfo` and keep one
named-query set per dialect. One call that returns the whole page is cheaper than five bindings.

**A pipeline holds no logic.** Alarm pipelines have no write API and no text form, so each script block is a one-line
call into a library function. The pipeline stays a Designer artifact; the logic stays versioned. Rosters exist in 8.3
scripting (`getRosters`, `createRoster`, no `deleteRoster`); pipelines can be listed but not created from a script
(ignition-api `alarm-scripting-surface.md`).

**Demonstrate alarm visuals without a real alarm.** Give the alarm frame component an optional `priorityOverride` param
so legends and palettes can force a priority; demo instances are configured like real ones but sit mid-band so nothing
ever fires.

**Built-in alarm tables replace custom ones.** `ia.display.alarmstatustable` and `alarmjournaltable` ship their own
detail modal and have no row-click event; build a bulk-action strip beside them instead of a custom table.

**Database connection minimums and the driver reference.** A SQLite connection needs about five fields; the gateway
back-fills the rest. Driver names are mixed case (`SQLite`) while translators are upper (`SQLITE`). The JDBC driver
resource lists valid driver names, class names, and URL formats for database types you have no example of. Encrypted
credential fields cannot be authored; pass plaintext on stdin or set them in the web UI (ignition-db
`connection-config-shape.md`).

## 10. Session state and user preferences

**A per-user UDT instance is the preference store.** A `User/Profile` type whose members are field types renders
automatically through the generic form renderer; adding a preference is adding a member. Field types are the end-user
extension point; core features use flat atomic members and purpose-built UI.

**Bound session props are `persistent: true`, and rare.** Unpersisted session-prop bindings occasionally fail to
execute. Expect the serialized last value to churn on every Designer save and ignore it in diffs.

**Tool pages that trigger project scans keep UI state in the session.** `system.project.requestScan()` remounts every
view and wipes view-scoped customs; durable UI state (`expanded`, `selected`) lives in session props, bidirectionally
bound from the view's customs.

**Never watch a transient interaction prop with `onChange`.** A property `onChange` and a page-scoped message handler
reacting to the same write run in that order, so the handler finds the state already cleared. Transient props (drag
source, hover target) may be bound to draw, never watched to react (ignition-view `onchange-vs-messages.md`).

**`page.custom` does not exist.** The page scripting object exposes no property trees; `self.page.custom` is `None`.
Page URL params land on the primary view's own `params`; a docked view reads `{page.props.path}` and decodes it itself.

## 11. Symbols, graphics, theming, and style classes

**One symbol wrapper routes; leaves self-bind.** `Pump/Symbol` is a pure router that embeds `{tagPath}.ui_symbolView`;
each leaf takes `tagPath` plus `orientation` and resolves its own state and appearance. Label, alarm frame, and hover
compose at the usage site.

**Appearance resolves in the leaf from an instance property with a session fallback.** `custom.appearance` is the
instance's value unless it is `auto`, in which case it follows the built-in `session.props.symbols.autoAppearance`
(`simple`, `p&id`, `mimic`). Variants gate `position.display` with a map keyed on that one value.

**Colorless SVG plus a colored style class.** Author `ia.shapes.svg` paths with geometry, opacity, and width only; a
class carrying `stroke` and `fill` paints them. Use the module's own symbol variables (`--symbolStroke--running`,
`--symbolFill--stopped`, `--pipeStroke`), which ship inside the Perspective module and are defined in no theme file, so
hand-drawn geometry tracks the stock symbols in every theme. Opacity is not a state channel (ignition-view
`svg-graphics.md`).

**One artwork per axis, CSS mirror for the opposite side.** A four-way orientable graphic ships two SVGs sharing a path,
gated by `lower(orientation)` plus a map transform, mirrored with `scaleX(-1)` or `scaleY(-1)`. `preserveAspectRatio:
"none"` turns a fixed path into a stretchable run.

**`ia.symbol.valve` orients via `props.valve`, not `props.orientation`.** The valve has no orientation prop; binding one
is a silent no-op. A blank valve on a cold session is a client-side sprite race, not a view bug; no view-level gate
fixes it (ignition-view `symbols.md`).

**A self-building palette discovers views by path convention and declared variants.** Equipment symbols are found at a
conventional path per type; built-in symbol wrappers declare their axes in `custom.variants` and the palette sweeps one
factor at a time. A representative demo instance per type lets tiles render honestly in any site.

**Fixed click contract on every tile family.** Label, graphic, and alarm frame open the detail popup; value readouts add
a pen to the shared ad hoc trend. Readouts use a generic `hover` class, never button chrome. Overlays own the click;
labels above them are `pointerEvents: none` (ignition-view `click-layering.md`).

**One class per state, swapped by a `style.classes` binding.** `variants[].pseudo` accepts only real CSS pseudo-classes,
never a custom state name. Compute the class string once on a view custom prop and property-bind it to every consumer; a
map transform with `outputType: "style-list"` is for a genuinely per-component enum (ignition-view
`style-class-state-binding.md`).

**Split classes so no two on one element set the same property.** Otherwise the outcome depends on stylesheet emission
order. `ia.display.label` writes its own inline color that a container class cannot cascade past, so row state on a
label needs bound color and weight.

**Portal-rendered chrome needs the stylesheet, not a class.** Dropdown option overlays, popup frames, scrollbars, label
ellipsis, and sparkline internals render outside the component subtree; reach them with prefixed `.psc-*` selectors in
the project stylesheet. Keep generated stylesheet regions fenced with markers and hand edits outside them.

**Color props take the bare token; CSS takes `var()`.** Component color props accept `"--neutral-90"`; only raw CSS
wraps it. Canvas charts (`ia.chart.*`) cannot read CSS variables at all and need literal hex. A class variant that must
beat an inline-bound style needs `!important`.

## 12. View authoring doctrine and the Designer round-trip

**Reach for the component event, not `onChange`.** `onActionPerformed` fires only on user interaction and cannot loop.
When `onChange` is unavoidable, guard with `if origin != "Browser": return`. `ia.input.text-field` has no
`onActionPerformed`; use `events.dom.onKeyDown` and test for `Enter`.

**Never pass an array as a view param.** Re-fires are missed when the length is unchanged. Params are scalars or config
dicts keyed `idx<n>_<name>` (a key must never start with a digit); a sibling `_<name>Example` param documents a dict's
shape and `_<name>s` lists an enum's legal values.

**Seed previews with typed mid-band values, never `null`.** A `null` seed carries no datatype, so formats and numeric
expressions blank out. Numbers mid-band, strings `""`, `tagPath` a live tag.

**Three kinds of stored prop value, three treatments.** A bound persistent prop's value is a volatile snapshot: ignore
it. An unbound persistent prop's value is the live mount seed: the Designer saves preview-mode writes into it, so diff
seeds on purpose after a Designer session and make transient state `persistent: false`. A bound gate prop must persist
its undecided sentinel; a `-1` to `1` flip flashes protected content before the check resolves (ignition-view
`persistent-props.md`).

**Bindings sit on the same components as the props they drive.** Component-level `propConfig` entries carry `persistent`
and `access` alongside the binding; flag-only entries are valid. Disable a binding in place with `enabled: false` rather
than deleting it.

**Views cannot nest inside another view.** A view at `A/B` when `A` is a view renders a dashed placeholder, silently;
validation reports clean. A path segment that holds views is a plain folder (ignition-view `view-nesting.md`).

**Generators seed a family once; the view file is truth afterward.** Never re-run a generator over a Designer-edited
view. Later changes are surgical load, modify, validate, write edits on the current file, with an exact round-trip lock
in tests so nothing is lost. When Designer edits reveal a better shape, update the generator even though it will not be
re-run.

**Diff Designer sweeps on purpose.** Look for persisted seeds on unbound props, `-1` to `1` flips on gate props,
`currentBreakpoint` on breakpoint containers, stripped defaults, and leaked test paths in input params.

**Capture hand edits back into the skill.** Snapshot before the human edits, diff after, and turn each semantic change
into a rule with a confidence grade. The human's edits are ground truth; the doc follows them (the `skill-learn` skill).

## 13. Agent workflow: dry-run, scan, logs, guards

**One writer for gateway files, and a missing verb is a bug in the writer.** Once every write to `projects/**` and
`config/resources/**` went through `ign`, every shape bug had one fix location and every write had validation, a dry
run, and a scan. When the CLI cannot express a shape, add the option (with a test), never a one-off script that calls
internals (ignition-disk `sole-writer-rule.md`).

**A dry run must show every file a real write emits and run the same validation.** A dry run that hid `resource.json`
could not preview the one attribute whose absence broke module loading, and one that skipped the tab and syntax gate
"passed" code the real write rejected. Audit every dry-run verb for both.

**Scan after every disk write, and print the scan result.** A verb that writes and auto-scans but prints only "written"
leaves the agent guessing whether the gateway accepted the change. Surface the scan response or a one-line status.

**Fixes land in the source a generator reads, never in its output.** A patch applied to a generated `view.json` was
reverted by the next regeneration; a test that checks script references caught it.

**Author-time guards beat runtime discovery.** Each class of silent failure (`==`, unbalanced braces, unknown function,
invalid icon name, snake_case prop, missing `typeId`, unresolved `typeId`) became a guard that raises with the problem,
the reason, and the fix. Guards sourced from the gateway (its icon sprite, its exports) rather than from guesses had no
false positives.

**Error messages name the problem, the reason, and the fix.** Fresh agents self-corrected from messages like "use
`readOnly`, not `read_only`; snake_case is silently kept as an unused prop" without reading source. Cryptic messages
send them into the code.

**Audit callers before changing a public helper's behavior.** Making a binding helper raise on constants, or a validator
reject a shape, broke existing call sites that relied on the old leniency. Grep and fix callers in the same change.

**A narrow symptom fix with the broadest change is the wrong fix.** An executor made two required fields optional to
unblock folder members, which reopened a silent-corruption path for a different tag type. Conditional validation by tag
type was the correct, smaller change. A test suite gate is the backstop.

**Scratch resources are removed the same session.** Probe views, diagnostic modules, and test instances that outlive a
session become log noise or duplicate resources. Mount, verify, delete, unmount, and clean the directory.

**Commit before ending a session; check for drift at the start of one.** A session that wrote to the gateway and updated
its ledger but did not commit left the repo and gateway inconsistent. Start by comparing untracked `projects/**` and
`config/resources/**` against the last recorded step.

**Correlate mechanism and target in a write guard.** A hook that blocked any command containing both a write character
and a protected path blocked `grep ... 2>/dev/null` and a commit message. Match a write mechanism whose argument is the
protected path.

**Escape square brackets in CLI help text.** A terminal help renderer that parses markup ate `[runtime]` from an install
hint, so the help told users the wrong command. Assert on help output in a test.

**Idempotent attach helpers by identity, not equality.** A factory that auto-attaches a component to the root, followed
by an explicit `add_to_<container>`, produced duplicate children in every non-flex container. Skip the append when the
same object is already a child; do not collapse two distinct but equal components.

## 14. Credential-safe tooling and OpenAPI-driven clients

**The token enters memory once, at client construction.** Set the `X-Ignition-API-Token: <name>:<secret>` header on a
long-lived HTTP client (not `Authorization: Bearer`); no call, path, log line, or exception message carries it. Tests
assert the key never appears in subprocess stdout or stderr (ignition-api `http-client-ban.md`).

**One sanctioned generic verb, no shell HTTP tools.** `ign api METHOD PATH` reads the token from `.env`; `curl` and
inline Python leak it into argv. Validate the path and method against the OpenAPI spec before sending, treat a literal
`{param}` in the path as an error, prompt before non-GET methods, and offer `--dry-run`.

**Refuse encrypted credential payloads everywhere.** Any body containing the JWE key set (`ciphertext`, `encrypted_key`,
`iv`, `protected`, `tag`) at any depth is rejected, both in the CLI and as an HTTP request hook. Credentials are set
through the Gateway UI (ignition-db `jwe-refusal.md`).

**Distinct exceptions for 401, 403, 400, 5xx, and transport failure.** 401 is a missing or bad token, 403 a token
without scope, 400 a bad payload whose body is worth printing. Render every error as `Error:` plus a one-line `Hint:`
and keep the handler order stable for log scrapers.

**Fetch the spec on first use, keyed by hash, never at import time.** The first typed verb, `ign api` path validation,
or `ign openapi docs` pulls `openapi.json` from the gateway into the state directory and generates the client; `ign
openapi fetch` only refreshes. Store a hash sidecar; regenerate only when the package is absent or the hash drifted.
Import the generated package lazily inside method bodies so a fresh clone still imports.

**Inject the shared transport into the generated client.** Use the plain `Client` with `set_httpx_client()` so auth and
the JWE guard apply to both the raw verb and the typed methods. The generated `AuthenticatedClient` adds a bearer header
that conflicts with the gateway's token header. Generated models are `attrs` classes; use `attrs.asdict`, not
`model_dump`.

**Generate the API reference from the same spec.** One markdown file per tag plus an index and an auth page rendered
from a template, because the spec declares no security schemes. Examples use an env-var placeholder, never a literal
token.

**Update and delete take a signature.** Fetch the resource first and pass its `signature` back; refuse to update with an
empty one.

## 15. Designing a typed generator for Ignition JSON

**Authoring models use `extra="forbid"`; only forward-compatible prop bags use `extra="allow"`, and those need a typo
guard.** Tag, alarm, UDT, and position models reject unknown keys loudly, which is right for a user's primary input.
Component props allow extras so unmodeled Perspective props still pass, which is why they need the snake_case check.

**Serialize with `exclude_none`, never `exclude_defaults`.** The gateway treats absent and defaulted differently for
some fields (`enabled: true` must be present on tags). `exclude_none` also drops an explicit `value: null` on a UDT
parameter; the gateway tolerated the absence, but emit it explicitly if a null default matters.

**Typed subclass props need `SerializeAsAny` in a children list.** A base `Component` with `children: list[Component]`
serializes typed subclass props against the base schema and warns; `list[SerializeAsAny[Component]]` fixes it.

**Discriminated unions on `type` map cleanly onto Ignition's handler and binding objects.** Events (`script`, `nav`,
`popup`), bindings (`tag`, `expr`, `property`, `query`, `tag-history`, `http`, `expr-struct`), and transforms (`map`,
`format`, `script`, `expression`) all discriminate on one key. A type alias for a nested dict (category to name to
handler) avoids the strict base model rejecting dict values.

**Corpus-coverage tests lock the model to the gateway.** For every strict model, a test that walks the on-disk corpus
and asserts every key and enum value used is modeled will fail before a false rejection reaches a user.

**Views cannot be checked at the top level by the component discriminator.** A view-level `propConfig` typed as a
pass-through dict lets a bad binding type through where the component-level union would reject it. Either type it or add
an explicit sweep.

**Schema validation is not gateway acceptance.** A model that validates can still reference a missing provider,
pipeline, or view. Parse the import response body for per-tag diagnostics even on 200, and validate rendered views
headlessly.
