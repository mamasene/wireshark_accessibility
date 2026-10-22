# Wireshark Accessibility

An NVDA add-on that makes the Wireshark graphical interface usable on Windows.

* Authors: Mama Sene, Emmanuel
* License: [GNU General Public License version 2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
* Requires NVDA 2024.1 or later; last tested with NVDA 2026.1
* Developed against Wireshark 4.6.8 on Windows 11

## Why this add-on exists

Blind network technicians generally fall back to **tshark**, the command-line
version of Wireshark, because several areas of the graphical interface are
poorly reported by a screen reader. The purpose of this add-on is not to
replace tshark, but to repair the graphical interface wherever the information
is actually there and simply not reaching NVDA.

Wireshark 4.6 is built with Qt 6 and exposes its interface through UI
Automation. Three families of defect follow from that, and all three have the
same shape: **the information exists in the accessibility tree, but not where
NVDA looks for it.**

## What it fixes

### The capture interface list

On the welcome page, Qt splits every row of the interface list into one cell
per column, and focus lands on a cell that holds no text. NVDA therefore had
nothing to announce, although the interface name sat in the neighbouring cell
of the same row.

Rows are now announced with the interface name and the position in the list,
for example *"Wi-Fi, 3 of 15"*.

### The packet list

The same cause, with seven columns: focus lands on the packet number, so NVDA
announced *"1"*, *"2"*, *"3"* and nothing else.

Rows are now announced with the frame number, the description of the packet and
the position:

> frame 3, 443 &rarr; 58388 [ACK] Seq=1 Ack=2 Win=15, collapsed, 3 of 18

The timestamp, source and destination are deliberately left out of that
automatic announcement. They are long digit strings that a speech synthesiser
spells out character by character, which is expensive to listen to while
scrolling and rarely what you need at that moment. They remain one keystroke
away, through the row reading command below.

The *collapsed* state is kept on purpose: it tells you the row carries a detail
tree, reachable with Tab.

### Buttons with no accessible name

Several Wireshark buttons expose no name at all, so NVDA announced only
*"button"*. Their tooltip is exposed as a description, and is already
translated by Wireshark: it is promoted to the name, and removed from the
description so it is not spoken twice.

### Links on the welcome page

The links in the *Learn* section — user documentation, wiki, questions and
answers, mailing lists — are Qt labels exposed as static text. NVDA treats
static text as layout, so it said nothing at all while Tab moved through them.
They are now presented as links and announced explicitly.

### Capture start and stop

Wireshark emits **no accessibility event** when a capture starts or stops. Two
separate event recordings established this: no name change, no state change.
Pressing `Ctrl+E` now reports *"Capture started"* or *"Capture stopped"*.

### Meaningless table coordinates

Qt exposes every tree row as a table cell, even in a tree that has a single
column. NVDA announced *"row 1, column 1"* on every field of the packet detail
tree. Those coordinates are now suppressed where the view really has one
column. The nesting level is kept, because there it distinguishes a protocol
from its fields.

## Commands

All commands are active only inside Wireshark, and all can be reassigned in
NVDA, Preferences, Input Gestures, under the **Wireshark** category.

| Shortcut | Effect |
|---|---|
| `Ctrl+E` | Start or stop the capture, then report the new state |
| `NVDA+Shift+C` | Report whether a capture is running |
| `NVDA+Shift+W` | Read the current row column by column, each value preceded by its column label |
| `NVDA+Shift+E` | Log the state of the Wireshark commands |

`Ctrl+E` is passed to Wireshark before anything else happens, so its behaviour
is unchanged whatever the add-on then does.

`NVDA+Shift+W` is where the columns left out of the automatic announcement come
back:

> No. 1, Time 0.000000000, Source 198.51.100.138, Destination 203.0.113.51,
> Protocol TLSv1.2, Length 104, Info Application Data

Column labels are read from the interface at run time, so they follow your own
column layout and your interface language. They are never assumed.

### Diagnostic commands, with no shortcut assigned

Three further commands serve the development of the add-on. They are
**deliberately left unassigned**: an accessibility recording should not be
triggerable by accident during a training session. Assign them in Input
Gestures if you need them.

* Log the accessibility information of the focused object
* Log the accessibility information of the navigator object
* Toggle logging of accessibility events

## Capture data is never written to the log

No recording writes capture data into the NVDA log. The text of packet rows,
packet details and statistics windows is replaced by a marker. Roles, states,
positions, automation identifiers and UIA patterns stay in clear, because that
is what diagnosis actually needs. The interface list is the one exception: it
holds device names, not traffic.

Row reading, by contrast, speaks everything. What is on screen belongs to the
user; only the log is protected, because the log travels.

## What is not fixed, and will not be

Wireshark paints the activity graph of the interface list with a delegate and
exposes **no value for it at all** — no name, no value, no description. This
add-on announces nothing about it. Deducing network activity from the
appearance of a graph would mean inventing data, which is exactly what a
network technician must never be given.

Per-interface throughput and packet counts remain the domain of tshark.

## Known issues to report upstream to Wireshark

* `interfaceTree` has no accessible name.
* The extcap and statistics cells of the interface list carry no
  `Qt::AccessibleTextRole`.
* Every button of the main toolbar shares the same automation identifier,
  `mainToolBar.QToolButton`, so none can be designated individually.
* The *Start* command is exposed as a check box while *Stop* and *Restart* are
  exposed as buttons.
* The packet list column headers are not translated, although the rest of the
  interface is.
* The four *Learn* links share the automation identifier `learnLink`, and
  neither their labels nor their descriptions are translated.

## Development

| Path | Role |
|---|---|
| `addon/appModules/wireshark.py` | The app module: every fix and every command |
| `addon/doc/fr/readme.md` | French user documentation |
| `docs/diagnostic-resultats.md` | Accessibility findings, with the measurements they rest on |
| `docs/protocole-diagnostic.md` | Step-by-step recording procedure |
| `tests/test_wireshark.py` | Test harness, runs without NVDA |
| `buildVars.py` | Build variables |

### Design principles

* Announcement fixes rely on **no event handler**: they act on the data NVDA
  reads, not on the moment it reads it.
* One key only is intercepted, `Ctrl+E`, and it is passed to Wireshark first.
* One timer only, the one that follows `Ctrl+E`, justified by the measured
  absence of any capture event. It starts on a user action, stops as soon as
  the state changes, and expires after seven and a half seconds. Nothing runs
  at rest.
* Controls are identified by markers taken from Wireshark's C++ source —
  automation identifiers, Qt class names — so they do not depend on the
  interface language. The capture state is read as a *state*, never as a label.
* Rows are identified by geometry, so the fixes survive a change in the number
  of columns, their order, or a live rebuild of the list.
* Nothing is announced that Wireshark does not actually expose.
* Only public NVDA APIs are used.

### Tests

```
python tests/test_wireshark.py
```

The harness replaces NVDA's modules with doubles and exercises the logic that
does not depend on them: splitting rows into cells, pairing column headers,
reading the capture state, redacting capture data. It runs on fake objects
reproducing the geometry and states actually measured in Wireshark 4.6.8.

### Building

```
pip install scons markdown
scons
```

The `.nvda-addon` file is produced at the root of the project.

## Translating

Source strings are English. To add a language, create
`addon/locale/<lang>/LC_MESSAGES/nvda.po` from `wiresharkAccessibility.pot`,
which `scons pot` generates, and an `addon/doc/<lang>/readme.md`. French is
supplied as a worked example of both.
