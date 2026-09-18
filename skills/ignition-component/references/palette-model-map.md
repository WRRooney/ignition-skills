# Type string to model class

Source files are under `ignition_gen_sdk/models/views/components/`. Each class
locks `type` with a `Literal` and pairs with a `<Class>Props` model.

## chart (`chart.py`)

| Type | Class |
|---|---|
| `ia.chart.chartrangeselector` | `ChartRangeSelector` |
| `ia.chart.gauge` | `Gauge` |
| `ia.chart.pie` | `Pie` |
| `ia.chart.powerchart` | `PowerChart` |
| `ia.chart.simple-gauge` | `SimpleGauge` |
| `ia.chart.timeseries` | `TimeSeries` |
| `ia.chart.xy` | `XY` |

## display (`display.py`, embedding in `embedding.py`)

| Type | Class | File |
|---|---|---|
| `ia.display.accordion` | `Accordion` | embedding.py |
| `ia.display.alarmjournaltable` | `AlarmJournalTable` | display.py |
| `ia.display.alarmstatustable` | `AlarmStatusTable` | display.py |
| `ia.display.audio` | `Audio` | display.py |
| `ia.display.barcode` | `Barcode` | display.py |
| `ia.display.carousel` | `Carousel` | embedding.py |
| `ia.display.cylindrical-tank` | `CylindricalTank` | display.py |
| `ia.display.dashboard` | `Dashboard` | display.py |
| `ia.display.equipmentschedule` | `EquipmentSchedule` | display.py |
| `ia.display.flex-repeater` | `FlexRepeater` | embedding.py |
| `ia.display.icon` | `Icon` | display.py |
| `ia.display.iframe` | `Iframe` | display.py |
| `ia.display.image` | `Image` | display.py |
| `ia.display.label` | `Label` | display.py |
| `ia.display.led-display` | `LedDisplay` | display.py |
| `ia.display.linear-scale` | `LinearScale` | display.py |
| `ia.display.map` | `Map` | display.py |
| `ia.display.markdown` | `Markdown` | display.py |
| `ia.display.moving-analog-indicator` | `MovingAnalogIndicator` | display.py |
| `ia.display.pdf-viewer` | `PdfViewer` | display.py |
| `ia.display.progress` | `Progress` | display.py |
| `ia.display.sparkline` | `Sparkline` | display.py |
| `ia.display.table` | `Table` | display.py |
| `ia.display.tag-browse-tree` | `TagBrowseTree` | display.py |
| `ia.display.thermometer` | `Thermometer` | display.py |
| `ia.display.tree` | `Tree` | display.py |
| `ia.display.video-player` | `VideoPlayer` | display.py |
| `ia.display.view` | `EmbeddedView` | embedding.py |
| `ia.display.viewcanvas` | `ViewCanvas` | embedding.py |

## input (`input.py`)

| Type | Class |
|---|---|
| `ia.input.barcodescannerinput` | `BarcodeScannerInput` |
| `ia.input.button` | `Button` |
| `ia.input.checkbox` | `Checkbox` |
| `ia.input.date-time-input` | `DateTimeInput` |
| `ia.input.date-time-picker` | `DateTimePicker` |
| `ia.input.dropdown` | `Dropdown` |
| `ia.input.fileupload` | `FileUpload` |
| `ia.input.multi-state-button` | `MultiStateButton` |
| `ia.input.numeric-entry-field` | `NumericEntryField` |
| `ia.input.oneshotbutton` | `OneShotButton` |
| `ia.input.password-field` | `PasswordField` |
| `ia.input.radio-group` | `RadioGroup` |
| `ia.input.signature-pad` | `SignaturePad` |
| `ia.input.slider` | `Slider` |
| `ia.input.text-area` | `TextArea` |
| `ia.input.text-field` | `TextField` |
| `ia.input.toggle-switch` | `ToggleSwitch` |

## navigation (`navigation.py`)

| Type | Class |
|---|---|
| `ia.navigation.horizontalmenu` | `HorizontalMenu` |
| `ia.navigation.link` | `Link` |
| `ia.navigation.menutree` | `MenuTree` |

## symbol (`symbols.py`)

| Type | Class |
|---|---|
| `ia.symbol.motor` | `Motor` |
| `ia.symbol.pump` | `Pump` |
| `ia.symbol.sensor` | `Sensor` |
| `ia.symbol.valve` | `Valve` |
| `ia.symbol.vessel` | `Vessel` |

`ia.symbol.valve` orients through `props.valve`; it has no `orientation`
prop, and binding one is a silent no-op.

## Fallback and non-components

- `GenericComponent` (`_generic.py`): any other `ia.*` string; `extra="allow"`.
- `Pipe`, `PipeOrigin` (`pipe.py`): entities in a container's pipe network;
  variant fields (`lineVariant`, `start`, `end`, `flanges`) pass through
  `extra="allow"`.
