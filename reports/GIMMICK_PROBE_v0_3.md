# NOXSUM Gimmick Probe v0.3 — LAN-01/02 + MIR-01/02

Status: exhaustive concept validation / not a Grant36 content change

This probe follows the v0.2 exploration direction:

- lantern + fixed NOX
- fixed-position rotatable mirror
- one new operation at a time
- unknown cells are not zero
- uniqueness is necessary but not sufficient
- the target feeling is "brief hesitation, then one clue makes the rest connect"

The frozen Grant36 campaign is not modified.

## Probe rules

### Lantern

- one lantern occupies one board cell
- it emits orthogonal rays up/down/left/right
- a SIT in the same row/column creates one shadow cell one step farther from the lantern
- the lantern itself creates no shadow
- SIT traces do not occlude each other
- unspecified observations are unknown

### Rotatable mirror

- one mirror has a fixed board cell
- the player chooses `/` or `\`
- fixed TOP light emits parallel downward beams
- the mirror bends a beam by 90 degrees
- a SIT creates one shadow cell immediately downstream for every beam path that reaches it
- the mirror occupies its cell and cannot also contain SIT

These are concept rules for exhaustive comparison, not yet canonical product rules.

## LAN-01 — CROSS THE CLUES

Inventory/state:
- fixed SIT C3
- movable SIT ×1
- lantern ×1
- no external light

Observed:

```text
    A B C D E
1   ? ? ? ? ?
2   ? ? ? ? 1
3   ? ? ? ? ?
4   ? ? 1 ? ?
5   ? ? ? ? ?
```

Solution:
- lantern C2
- movable SIT D2

Reasoning:
1. C4=1 can be made by fixed C3 only when the lantern is above C3.
2. E2=1 needs a SIT at D2 illuminated from its left.
3. The intersection is lantern C2.
4. The movable SIT is therefore D2.

Exhaustive search:
- legal states: 552
- C4 only: 48 survivors
- E2 only: 5 survivors
- C4 + E2: **1 survivor**

This is the rule-readable lantern puzzle. Neither clue alone specifies the state.

## LAN-02 — KNOWN TRACE, UNKNOWN LIGHT

Inventory/state:
- fixed SIT C3
- movable SIT ×1
- lantern ×1
- no external light

Observed:

```text
    A B C D E
1   ? ? ? 1 ?
2   ? ? ? ? ?
3   ? 1 ? ? ?
4   ? ? ? ? ?
5   ? ? ? ? ?
```

Solution:
- lantern D3
- movable SIT D2

Reasoning:
1. One SIT can contribute at most one shadow under this lantern model.
2. The two observed marks therefore need the fixed and movable SIT to contribute separately.
3. Fixed C3 cannot make D1, so it must explain B3.
4. B3 requires illumination from the right of C3, narrowing the lantern to D3/E3.
5. D1 then forces movable SIT D2 and lantern D3.

Exhaustive search:
- legal states: 552
- B3 only: 48 survivors
- D1 only: 5 survivors
- B3 + D1: **1 survivor**

This preserves the LN-PROBE-01 result as the AHA candidate.

## MIR-01 — TURN THE BEAM

Inventory/state:
- fixed mirror C3
- mirror orientation `/` or `\`
- movable SIT ×1
- fixed TOP light

Observed:

```text
    A B C D E
1   ? ? ? ? ?
2   ? ? ? ? ?
3   1 ? ? ? ?
4   ? 1 ? ? ?
5   ? ? ? ? ?
```

Solution:
- mirror `/`
- movable SIT B3

Reasoning:
1. B4=1 is the ordinary TOP shadow of SIT B3.
2. With SIT B3 fixed by that clue, only `/` sends the C-column beam left through B3.
3. That reflected path creates A3=1.

Exhaustive search:
- legal states: 48
- A3 only: 3 survivors
- B4 only: 2 survivors
- A3 + B4: **1 survivor**

The intended lesson is not "learn a new reflection formula by text"; it is "one SIT can answer two marks because one beam was bent."

## MIR-02 — THE SHADOW THAT MUST NOT EXIST

Inventory/state:
- fixed mirror C3
- mirror orientation `/` or `\`
- fixed SIT B3
- movable SIT ×1
- fixed TOP light

Observed:

```text
    A B C D E
1   ? ? ? ? ?
2   ? ? ? ? ?
3   0 ? ? ? ?
4   ? ? ? ? ?
5   ? ? ? ? 1
```

Solution:
- mirror `\`
- movable SIT E4

Reasoning:
1. E5=1 forces the movable SIT to E4 under the fixed TOP light.
2. With E4 known, **both mirror orientations still survive**.
3. Fixed SIT B3 is now the orientation probe.
4. If the mirror is `/`, the reflected C3 beam travels left through B3 and creates A3=1.
5. The record explicitly says A3=0, so `/` is impossible.
6. Therefore the mirror must be `\`.

Exhaustive search:
- legal states: 46
- E5 only: **2 survivors**, exactly one for each mirror orientation
- A3=0 only: 22 survivors
- E5 + A3=0: **1 survivor**

This is the strongest result of the four concept probes because ZERO is doing real causal work. The second observation is not another positive mark to chase; it forbids a reflected path.

## Result table

| Probe | Search space | One clue | Other clue | Both | Intended role |
| --- | ---: | ---: | ---: | ---: | --- |
| LAN-01 | 552 | 48 | 5 | **1** | lantern rule read |
| LAN-02 | 552 | 48 | 5 | **1** | fixed NOX as light-source evidence |
| MIR-01 | 48 | 3 | 2 | **1** | mirror rotation rule read |
| MIR-02 | 46 | 2 | 22 | **1** | AHA / ZERO rejects reflected path |

## What the exhaustive search does and does not prove

It proves:
- every authored state is legal under the stated probe rules
- each two-clue problem has exactly one solution
- each clue has a measurable role
- MIR-02 really has a two-way orientation ambiguity before ZERO is read

It does not prove:
- the lantern's four-ray behavior is visually intuitive
- mirror paths are pleasant to trace on the real UI
- the problems feel good rather than merely being unique
- these mechanics belong in MOBILE100

The next gate is human playtest.

Suggested order:
1. LAN-01
2. LAN-02
3. MIR-01
4. MIR-02

For each, record the first spontaneous explanation after solve. The success signal is a short causal sentence, not "I tried every square."
