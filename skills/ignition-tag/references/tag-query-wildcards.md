# `system.tag.query` path wildcards are recursive and contains-match

Verified against the gateway's own `common.jar`.

- A condition `path: "<root>/*"` routes through a wildcard matcher whose test
  is a regex match against the whole source-less path. `*` and `%` map to
  `.*`, `?` to `.`, the rest is quoted, and the pattern is wrapped in
  `.*...*` and compiled case-insensitive.
- Consequence one: the wildcard crosses `/`, so one query already reaches
  every level. Do not add `system.tag.browse` recursion or per-level queries;
  they are dead code.
- Consequence two: it is a contains match, not a prefix match.
  `[default]OtherArea/Area1/...` matches a root of `Area1`. Always post-filter
  `fullPath.startswith(rootPath + "/")`.
- A provider-qualified root (`[default]Area1`) is correct in the condition;
  the provider is stripped before matching.
- Combine with a `hierarchy` condition (`[{"typeId": "Nav/_Nav",
  "relationship": "SubType"}]`) anchored on an abstract base type to find every
  instance of a family in one call; unlike `system.tag.browse`'s `typeId`
  filter, it matches types nested under folders. Add `returnProperties` to
  fetch custom properties without a second read (`tag-query-alarm-attribute.md`
  lists the other condition fields).
- Derive nesting from the returned `fullPath`: relative path, depth (folder
  count), parent path, and label folder. Deep nesting costs nothing.

## Guards

- Discovery that runs `system.tag.getConfiguration(path, True, False)` on an
  empty path reads the whole provider recursively; guard the path first. The
  view-side rule is in the ignition-view skill
  (`discovery-transform-null-guard`).
- In an unauthenticated session, `getConfiguration` returns nothing when the
  provider requires an authenticated security level for edit or write; read
  binds still work but discovery is empty. Validate discovery in an
  authenticated session.
