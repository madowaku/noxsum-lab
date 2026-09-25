# NOXSUM LAB SPEC v0.1

## 1. Purpose

NOXSUM 本体からレベル研究を分離し、問題を大量に作って壊して比較できる場所を作る。

Lab の成果物は「生成コード」ではなく、最終的には **採用に値する問題と、その理由を説明できるデータ**。

## 2. Product split

### Mobile = FLOW
- 初手が見つかりやすい
- 盤面が一気に進む瞬間がある
- 30秒〜3分程度を主戦場にする
- 最後の配置 / 回転が「カチッ」と決まる
- 連続プレイしたくなる

### Steam = AHA
- 推論が一段深い
- 一度見方を変える必要がある
- 解けなくてもヒントや解説で納得できる
- 「難しい」より「気づくと美しい」を優先する
- 総当たり依存は高難度として評価しない

## 3. Pipeline

1. Generate
2. Solve / Validate
3. Deduplicate
4. Analyze
5. FLOW / AHA scoring
6. Human playtest
7. Curate
8. Export

## 4. Source identity

生成された問題は `NX-GEN-xxxxxx` のような source id を持つ。

製品採用時には別IDを付けても source id は残す。

例:

```text
NX-GEN-004821
  ├─ Steam: STEAM-2-07
  └─ Mobile: MOBILE-0137
```

変異問題は parent id も保持する。

## 5. Canonical level

ゲーム側の保存形式をそのまま研究DBにはしない。

Lab では `schemas/noxsum_level_v1.schema.json` を canonical schema とし、ゲーム側の現行 Grant JSON は importer で変換する。

Canonical 側は以下を分離する。

- puzzle definition
- mechanics
- solution
- provenance
- automatic metrics
- human curation

これによりゲーム本体のJSON形式が変わっても研究履歴を残せる。

## 6. Human curation

最低限の人間評価:

- `FLOW`
- `AHA`
- `BOTH`
- `REJECT`

追加タグ候補:

- `stand_breakthrough`
- `rotation_finish`
- `forced_first_move`
- `false_lead`
- `multiple_observation`
- `elegant_constraint`
- `bruteforce_smell`

## 7. v0.1 exit criteria

- 現行 Grant JSON を canonical level へ import できる
- canonical schema validation が通る
- source id / parent id を保持できる
- FLOW / AHA / human tags を保存できる
- Steam / Mobile の export 先を区別できる

Solver / Generator の高度化はこの土台の上に追加する。
