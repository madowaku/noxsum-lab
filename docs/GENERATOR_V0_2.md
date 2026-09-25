# NOXSUM Generator v0.2

## Goal

大量生成そのものではなく、**Mobile向けのFLOW問題**と**Steam向けのAHA問題**を同じ鉱山から別々に発掘する。

v0.2 は次の順で処理する。

```text
10,000 exact-unique candidates
  ↓
D4 symmetry canonicalization
  ↓
reasoning / texture features
  ↓
FLOW score + AHA score
  ↓
two independent rankings
  ↓
human playtest
```

スコアは品質の判定ではない。人間が遊ぶ候補を絞るための探知機として使う。

## Mining profiles

デフォルトでは6種類のinventoryと4種類の照明クラスを組み合わせた24 profileを均等に掘る。

Inventory:

- N3 / T0 / P0
- N4 / T0 / P0
- N2 / T1 / P0
- N3 / T1 / P0
- N2 / T0 / P1
- N1 / T1 / P1

Light class:

- adjacent 2 lights: TOP + LEFT
- opposite 2 lights: TOP + BOTTOM
- 3 lights: TOP + LEFT + RIGHT
- 4 lights

回転・反転で等価な照明方向をすべて別profileにはしない。

## Symmetry dedupe

正方形のD4対称群8種を使う。

- identity
- 90 / 180 / 270 degree rotations
- horizontal / vertical reflection
- two diagonal reflections

盤面だけでなく**targetとlight directionを同時に変換**する。

したがって、盤面を90度回転し、ライトも90度回転しただけの問題は同じcanonical puzzleとして扱う。

Inventoryが違う問題は別問題として残す。

## Reasoning features

### Search-space features

- `search_space`
- `best_single_survivors`
- `median_single_survivors`
- `best_pair_survivors`
- `opening_strength`
- `pair_strength`
- `pair_synergy_bits`

### Greedy witness

全25セルを最初から見せる実ゲームとは別に、「どのセルの情報が候補を最も減らすか」を順に選ぶ解析用traceを作る。

- `witness_length`
- `first_greedy_survivors`
- `penultimate_survivors`
- `max_information_gain`
- `late_max_information_gain`

これはプレイヤーの実際の思考順を断定するものではない。問題内のconstraint structureを見る近似指標。

### Texture

- `visible_nonzero_cells`
- `zero_cells`
- `overlap_cells`
- `max_shadow_value`
- `total_shadow_ink`
- `target_entropy`
- `solution_span`
- `solution_center_distance`
- `edge_loss`

## FLOW score v0.2

Mobile候補。

高く評価する傾向:

- 明確なとっかかりがある
- 推論列が短〜中程度
- 最後に2〜5候補程度の小さな曖昧さが「カチッ」と消える
- 適度なoverlap
- 盤面が単調すぎない

単純すぎても、長すぎても満点にはしない。

## AHA score v0.2

Steam候補。

高く評価する傾向:

- 単一セルだけでは決まりすぎない
- 2つ以上のconstraintを合わせると候補が大きく減る
- 中程度以上の推論深度
- 後半に大きなinformation gainがある
- overlapが意味を持つ

長いだけの問題は評価しない。

`witness_length` が極端に長い場合は `bruteforce_smell` として減点する。

## Automatic tags

現状:

- `clear_foothold`
- `constraint_synergy`
- `snap_finish`
- `late_breakthrough`
- `overlap_rich`
- `deep_chain`
- `bruteforce_smell`

## Human loop

自動ランキング後の最終判定は人間。

### Mobile

```text
FLOW top candidates
  ↓
madowaku playtest
  ↓
気持ちいい / 普通 / 捨て
  ↓
Mobile pack
```

### Steam

```text
AHA top candidates
  ↓
madowaku first attempt
  ↓
解けない場合はsolution / explanationを見る
  ↓
「なるほど！」なら採用候補
  ↓
Steam chapter design
```

将来はこの人間評価を教師データとしてv0.3以降のscoreへ戻す。
