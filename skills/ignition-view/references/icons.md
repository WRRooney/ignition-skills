# Icons

## Where the sprites live in 8.3

8.1 kept icon sprites on disk under `webserver/webapps/main/res/perspective/icons/`.
8.3 does not; they ship inside the module:

```
user-lib/modules/Perspective-module.modl        (zip)
  perspective-icons-<version>.jar               (zip)
    icons/material.svg      ~1300 glyphs        ia.display.icon set
          ignition.svg      3 glyphs            ia.display.icon set
          symbol_simple.svg / symbol_p&id.svg / symbol_mimic.svg   ia.symbol.* artwork
```

Two traps:

1. They are `:target` sprites, not `<symbol>` sheets. Each glyph is
   `<g class="icon" id="NAME">`; a `<symbol id=...>` regex returns zero and reads
   as "this version ships no icons".
2. The `symbol_*` sheets use nested `<svg id=...>` and are addressed by the
   `ia.symbol.*` components, not by an icon path.

## Listing them

```bash
ign icons list                               # material names, one per line
ign icons list --set all                     # count per set
ign icons list --set ignition --json
ign icons list --modl /path/Perspective-module.modl
ign icons list --container <docker-container> # copies the module out with docker cp
```

The module is read via `docker cp`, never `docker exec cat`: exec mangles the
binary stream quietly, both zips still open, and every sprite reads back empty.
The gateway HTTP API cannot serve `/res/perspective/icons/...`.

## An invalid path crashes the component

An `ia.display.icon` whose `props.path` is not in the bundled set (the classic
material set; the newer Material Symbols names such as `material/water_drop` are
absent) renders nothing and crashes the component with
`React.cloneElement(...): The argument must be a React element, but you passed null`
in the browser console, while passing every model check. `ViewBuilder.icon(path=)`
rejects an unknown `material/<name>` at author time from a whitelist
(`ignition_gen_sdk.validation.material_icons.MATERIAL_ICONS`); regenerate it from
`ign icons list` if the gateway's module version differs.

`ign view validate` counts the console error, so probing a screen of candidate
names gives the missing count from the console and the missing names from the
screenshot.

## Empty embed path logs the same error

An `ia.display.view` with an empty `props.path` logs the same `cloneElement`
error. Model an optional embed as a flex repeater with zero instances instead of a
hidden view with no path.
