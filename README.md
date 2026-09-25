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

## Curation principle

難しい問題がそのまま Steam 向けとは限りません。

- **FLOW**: 初見で気持ちよく進み、最後の一手が「カチッ」と決まる
- **AHA**: 解けなくても解説・ヒントを読んだ瞬間に「なるほど！」が起きる
- **REJECT**: 総当たり頼み、冗長、解説を読んでも納得感が弱い

## Compatibility

初期段階では現在の NOXSUM / Grant データ形式を importer で読み込み、Lab 内部では拡張可能な canonical level 形式へ変換します。

今後の SIT / STAND / WARK、FIXED NOX、SWITCH、BLOCKER、MIRROR なども canonical schema を拡張して扱います。

## Status

**v0.1 bootstrap**

最初の到達点は「既存問題を import → 検算 → 特徴量を付与 → FLOW/AHA 候補として export」できることです。
