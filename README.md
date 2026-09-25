# NOXSUM Lab

NOXSUM の問題を **生成・検算・分析・選抜**するための研究用リポジトリです。

ゲーム本体は `madowaku/shadow-sum`（NOXSUM）側に置き、この repo は大量の候補問題を扱う「鉱山 / 研究所」として分離します。

## Goals

- 大量生成した問題を Solver で検算する
- 重複・退屈な問題を自動で落とす
- 問題の特徴量を記録する
- **FLOW**（モバイル向けのサクサク感）と **AHA**（Steam向けの発見）を別軸で評価する
- 人間のプレイテスト評価を蓄積する
- 採用問題だけを製品 repo へ export する
- 生成元 / 変異元を追跡できる「問題の出生証明書」を残す

## Repository boundary

### noxsum-lab
- generator
- solver
- analyzer / scorer
- mutation
- duplicate detector
- playtest metadata
- candidate pools
- export tools

### NOXSUM game repo
- Godot game
- presentation
- Steam / Mobile campaign
- 採用済み level pack のみ

## Current reference campaign

Grant 最終版は **GR01〜GR36**。

Lab には `fixtures/grant36_v0_5.json` としてスナップショットし、CIで36問すべてを独立Solverから全探索して一意解と解答メタデータを再検算します。

現行ルールとして扱うもの:

- Normal Post
- Tall Post
- rotatable Plate
- TOP / LEFT / RIGHT / BOTTOM lights
- free light selection
- fixed / movable shutter
- FOG
- boardShape socket mask

## v0.1 pipeline

```text
Generate
  ↓
Validate / Solve
  ↓
Deduplicate
  ↓
Analyze
  ↓
FLOW / AHA scoring
  ↓
Human playtest
  ↓
Curate
  ↓
Export → Steam / Mobile
```

## Commands

```bash
python -m pip install -e .

# Grant最終36問を独立再検算
noxsum-lab revalidate-grant fixtures/grant36_v0_5.json

# seed付きGenerator v0.1
noxsum-lab generate generated/sample.json \
  --seed 20260925 \
  --count 20 \
  --normal 3

# Tall / Plate 混成も生成可能
noxsum-lab generate generated/mixed.json \
  --seed 20260925 \
  --count 20 \
  --normal 1 \
  --tall 1 \
  --plate 1 \
  --lights TOP,LEFT,RIGHT,BOTTOM

# canonical schema検証
noxsum-lab validate generated/sample.json
```

Generator v0.1 は「解答配置をランダムに置いて終わり」ではなく、指定profileの合法世界を列挙し、**同じ観測を作る世界が1つだけの target** のみを候補として出力します。同じseed + profileなら同じ候補列になります。

## Curation principle

難しい問題がそのまま Steam 向けとは限りません。

- **FLOW**: 初見で気持ちよく進み、最後の一手が「カチッ」と決まる
- **AHA**: 解けなくても解説・ヒントを読んだ瞬間に「なるほど！」が起きる
- **REJECT**: 総当たり頼み、冗長、解説を読んでも納得感が弱い

## Compatibility

現在の NOXSUM / Grant データ形式は Solver が直接検算でき、importer から Lab の canonical level 形式へ変換できます。

今後の SIT / STAND / WARK、FIXED NOX、SWITCH、BLOCKER、MIRROR なども canonical schema と rules layer を拡張して扱います。

## Status

**v0.1: rules + solver + seeded generator**

次の主戦場は、生成候補から「気持ちいい」と「なるほど」を掘り分ける FLOW / AHA scoring です。
