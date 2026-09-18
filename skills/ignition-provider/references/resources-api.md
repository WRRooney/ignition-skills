# The gateway resources API (pointer)

Tag providers share the `/data/api/v1/resources/ignition/<type>` family with
database connections, alarm journals, and every other config resource. The
canonical rules live in the ignition-api skill:
[`resources-array-body.md`](../../ignition-api/references/resources-array-body.md).

In short: `POST` and `PUT` take a JSON **array** body even for one resource
(a bare object is `400 Not a JSON Array`); the element is `{name, enabled,
description, config: {profile, settings}}` plus the current `signature` on
update and delete; `?allowInvalidReferences=true` defers reference validation;
resources register live and the trailing `/scan/config` only reconciles disk.
`ign provider create/update/delete` build the envelope and fetch signatures for
you; `ign provider describe` is `GET /resources/type/ignition/tag-provider`.
