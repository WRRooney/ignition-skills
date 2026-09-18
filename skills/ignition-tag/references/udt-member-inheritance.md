# UDT member inheritance and `valueSource`

## Types inherit through `typeId`

On a `UdtType`, `typeId` is the parent type's path (for example `"_Base"` or `"Equipment/Motor"`). Members are inherited from the parent; a child does not repeat the parent's members. A member override in the child carries only the keys that change:

```json
{"name": "Pump", "tagType": "UdtType", "typeId": "Equipment/Motor",
 "tags": [{"name": "Speed", "tagType": "AtomicTag", "dataType": "Float8"}]}
```

Here `Speed` inherits `valueSource` (and everything else) from `Equipment/Motor`'s `Speed` member and only changes `dataType`. The SDK models this with `UdtMemberTag`, the `Tag` schema relaxed for member context: optional `dataType` and `valueSource`, flat `meta_*` extras allowed, bound parameter values allowed.

## When a member still needs `valueSource` and `dataType`

- A new member declared in the type that no parent supplies.
- Any member of a type with no `typeId`.

Use `"memory"` for in-type memory members, `"expr"` plus `expression` for expression members, `"reference"` plus `sourceTagPath` for references, `"opc"` plus `opcServer` and `opcItemPath` for OPC members.

## Instances cannot add members; declare them on the type

A UDT instance overrides the values of members its type declares. It cannot
add ad-hoc child tags inside a type-declared folder: shipping a base type with
an empty `Setpoints/` folder and expecting each instance to add `SpeedSP` under
it fails (the import reports a failure for the extra tag, and a faceplate that
browses `<instance>/Setpoints` finds nothing). Keep the base type minimal and
declare the real members on a child type (`typeId: "Base/Equipment"`, members
with `dataType`, `valueSource`, `value`); instances then override only values,
and a faceplate that browses whatever the type declares stays uniform across
base and child types.

## Standalone tags are strict

A standalone `AtomicTag` sent through `ign tag build` or `ign tag push` must carry both `dataType` and `valueSource`. Only `Folder` nodes and UDT member tags may omit them. The error is `AtomicTag '<name>' requires dataType and valueSource`.

## Override kind quirk

The Designer writes an override of an inherited member as `"tagType": "AtomicTag"` with only the changed keys, even when the member is really a `UdtInstance` (for example flipping `enabled` on a nested alarm instance, or adding `meta_*` layout on it). This is not a kind change; the models accept an `AtomicTag`-kind, keys-only override of an instance member. The Designer also name-sorts `tags` arrays and writes whole-number history properties as integers (`historyMaxAge: 1`), so expect that churn when diffing against a Designer save.

## Indirect tag bindings in Perspective

Two valid forms when a view binds into a UDT instance by parameter:

- Numbered: `tagPath: "{1}/Speed"` with `references: {"1": "{view.params.path}"}`.
- Named: `tagPath: "{tagPath}.meta_label"` with `references: {"tagPath": "{view.params.tagPath}"}`.

A bare `{param}` token is malformed only when no `references` entry resolves it. The view builder's `bind_custom_tag` auto-numbers; pass `references={...}` for the named form.
