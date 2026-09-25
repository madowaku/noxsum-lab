# FLOW 20 + AHA 20 Blind Playtest Pack v0.1

## Purpose

Generator v0.2 の FLOW / AHA score が、実際のNOXSUMの気持ちよさ・発見感と一致しているかを、人間評価で校正する。

## Selection

各軸20問。

### FLOW
- ELITE: rank 1-50 から8問
- STRONG: rank 51-200 から6問
- MID: rank 201-600 から4問
- CONTROL: rank 601-1500 から2問

Eligibility:
- witness 3-9
- penultimate survivors 2-6
- bruteforce_smell は除外

### AHA
- ELITE: rank 1-50 から8問
- STRONG: rank 51-200 から6問
- MID: rank 201-600 から4問
- CONTROL: rank 601-1500 から2問

Eligibility:
- witness 4-10
- pair synergy >= 1.0 または late information gain >= 4.0
- bruteforce_smell は除外

## Diversity caps

同じ型だけが上位を独占しないよう、選抜時に以下を制限する。

Strict pass:
- exact profile: 最大2問
- inventory: 最大5問
- light class: 最大8問

不足時だけ fallback:
- exact profile: 最大3問
- inventory: 最大6問
- light class: 最大10問

## Blind order

FLOW / AHA のラベルを削除し、PT-001〜PT-040へ振り直す。

- FLOW 20 / AHA 20
- 同一区分が3問以上連続しない
- 可能な限り直前と同じprofileを避ける
- source id / rank / score / tags は公開packから削除

答え合わせ情報は _DO_NOT_OPEN ファイルに分離する。

## Human ratings

全40問について区分を知らずに同じ軸で評価する。

- solved_without_reveal
- time_seconds
- flow_feel_1_5
- aha_1_5
- frustration_1_5
- want_next_1_5
- reveal_reaction
  - NA
  - NARUHODO
  - FLAT
  - UNFAIR
- notes

## Why bands?

上位20問だけを評価すると「上位候補の平均」しか分からない。

ELITE / STRONG / MID / CONTROL を混ぜることで、score と人間評価が実際に相関しているかを測る。

## v0.3 input

プレイテスト後は answer key と ratings.csv を join し、以下を調べる。

- FLOW score vs flow_feel
- FLOW score vs want_next
- AHA score vs aha
- AHA score vs NARUHODO rate
- witness_length vs frustration
- pair_synergy vs aha
- penultimate_survivors vs flow_feel
- profile / inventory / lights ごとの偏り

v0.3では、人間評価を優先して重みを再調整する。
