# Style classes, stylesheet, and themes

```bash
ign style-class list --project Demo
ign style-class write --project Demo --name state-running --file /tmp/running.json   # {"base": {"style": {...}}, "variants": [...]}
ign style-class write --project Demo --file /tmp/family.json                           # {"name": payload, ...} bulk
ign style-class delete --project Demo --name state-running

ign stylesheet show --project Demo
ign stylesheet upsert --project Demo --marker pump-flash --file /tmp/flash.css          # replaces only that block
ign stylesheet remove --project Demo --marker pump-flash

ign theme list
ign theme copy-base                                                  # read-only copies of light/dark to learn token names
ign theme write --name plant-dark --dir /tmp/plant-dark --entrypoint index.css --description "..."
ign theme delete --name plant-dark
```

`style.json` carries only `base` and `variants`; any other key fails loud.
`variants[].pseudo` accepts CSS pseudo-classes only (`hover`, `disabled`, ...), so
data-driven state is one class per state plus a `style.classes` binding
(`style-class-state-binding.md`). Stylesheet selectors use the
`.psc-<class>` prefix; view JSON references the class unprefixed. The stylesheet is
the only channel for `@keyframes` because `ia.display.markdown` strips `<style>`.
Copies made by `theme copy-base` are ignored by the gateway; put overrides in a
theme of your own that `@import`s them.
