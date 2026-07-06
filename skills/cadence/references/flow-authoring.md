# flow-authoring — ドメインフローの作り方（PJ の蓄積知識をフローに蒸留する）

cadence の実行エンジンと規約は汎用だが、**強さの源泉はフローに書かれたドメイン知識**
（観点リスト・品質基準・そのPJで実際に踏んだ失敗モード）にある。このガイドは、
既に知識が溜まっている PJ（NOTES.md・checkpoints・過去のインシデント）から
ドメインフローを蒸留する手順を定める。

## 置き場所（重要）

```
<PJ>/.claude/cadence/
├── flows/<name>.md        # ドメインフロー（PJ のリポでコミット・版管理する）
└── personas/<name>.md     # PJ 固有ペルソナ（supervisor/planner 等の共通ペルソナは
                           # グローバル側が使えるので、固有の監査者役だけ置けばよい）
```

- **`.cadence/`（ラン成果物・gitignore）とは別物**。フローは資産なので `.claude/cadence/` に置いてコミットする。
- **cadence リポ（public）には持ち込まない**。業務ドメインの知識・固有名詞は各PJのリポに閉じる。
  PJ のリポと一緒に各PCへ移動するので、マルチPC運用でも配布の仕組みは不要。
- エンジンはフロー名を〔PJ ローカル → 同梱〕の順で解決する。同名なら PJ 側が勝つ。

## いつ作るか（作らない判断も含む）

作る価値があるのは次を**全て**満たす業務：
1. **繰り返し発生する**（同型の監査・調査・レビューを2回やった。3回目の前に作る）
2. **判断が重く、完成の定義が言語化できる**（「何をもって issue-ready か」が言える）
3. **経験由来の観点がある**（実際にハマった・見逃した記録が NOTES.md や checkpoint にある）
4. **モデルの一般知識との差分が大きい**（世間のベストプラクティスでなく、そのPJ固有の環境・基準・失敗モード）

1つでも欠けるなら作らない。観点が経験由来でないフローは「余計な手順のついた汎用プロンプト」にしかならない。

## 蒸留手順（既存PJへの導入セッションでやること）

対象PJ上の Claude Code セッションで、以下を順に行う（通常の会話でよい。cadence で回す必要はない）：

1. **原料を読む**：PJ の `NOTES.md`（罠・ハマりどころ・設計判断）、`docs/checkpoints/` の失敗・手戻りの記録、
   `REQUIREMENTS.md` の品質要件。「あの時これも見ておけば」の類を全部拾う。
2. **観点リストに変換する**：拾った教訓を「監査/調査時に必ず確認する観点」の形に書き直す。
   固有名詞（対象システム・ファイル・環境）を残すこと——そこが汎用機能に勝つ部分。
3. **品質基準を定義する**：その業務の「issue-ready」は何か。finding に何が揃えば行動可能か
   （`references/report-template.md` を業務に合わせて具体化）。
4. **リスク体制を選ぶ**：`mode: read-only` か `mode: edit`＋有人承認か。ライブ状態（MCP）との突合が要るか。
   決定論ゲートにできる検証（テスト・lint・整合チェック）はあるか。
5. **フローを書く**：下のテンプレートを埋める。step 構成は迷ったら同梱フローの型
   （plan → 本体 → supervise ↔ review）をそのまま使う。凝った遷移より観点リストの質に時間を使う。
6. **機械検証する**：`python3 <cadenceリポ>/scripts/validate-flows.py --project-dir <PJルート>`
7. **PJ の CLAUDE.md にトリガを登録する**：ユーザーが「cadenceで」と言い忘れても提案される
   ように、PJ の CLAUDE.md に1-2行足す。例：
   > `〜の監査/調査の依頼が来たら、着手前に「/cadence <flow名> で回しますか？」と提案する。`
   （グローバル側には汎用の cadence トリアージが入っている——install.sh が注入する
   `rules/cadence-triage.md`——が、PJ 固有フローの存在と発動条件は PJ 側にしか書けない。）
8. **1回実走して育てる**：初版は必ず穴がある。実走で出た「見逃し・過剰指摘・不便」を
   フローの観点リストに**その場で**反映する（PJ側の資産なので直接編集してコミット）。

## フローテンプレート

```markdown
# flow: <name>

​```yaml
purpose: >
  <この業務は何か・何を出力するか・何を変更しないか>
mode: read-only            # or edit（edit なら require_human_approval: true）
initial: plan
max_cycles: 3              # ハードキャップ。到達で必ず停止
​```

## steps

### plan
- **persona**: planner            # 共通ペルソナはグローバル側を参照できる
- **edit**: no
- **instruction**:
  - <サーフェスの列挙：このPJで見るべき対象を固有名詞で>
- **next**:
  - スコープ明確 → `audit`
  - 情報不足 → `ABORT`

### audit
- **persona**: <domain-persona>   # PJ 固有の監査者。personas/ に置く
- **edit**: no
- **parallel**: 3                 # 任意
- **mcp**: <server>               # 任意。ライブ突合するなら（read-only のみ）
- **instruction**:
  - <★ここが本体：経験由来の観点リスト。「必ず確認する」項目を具体的に>
  - <各 finding の必須項目（安定ID・場所・シナリオ・影響・修正案）>
- **next**:
  - 完了 → `supervise`

### supervise
- **persona**: supervisor
- **edit**: no
- **instruction**:
  - <このドメインの「完成」の定義で被覆と issue-ready を判定>
- **next**:
  - 十分 → `COMPLETE`
  - ギャップあり（budget 内） → `review`
  - 停滞/上限 → `ABORT`

### review
- **persona**: <domain-persona>
- **edit**: no
- **instruction**:
  - supervisor 指摘のギャップを埋める。audit と同じ様式。
- **next**:
  - 済 → `supervise`

## convergence
max_cycles はハードキャップ。上限前でも finding ID 集合に差分が無ければ早期 ABORT。

## gates（任意）
<決定論化できる検証があれば references/gates.md の書式で>
```

## ペルソナテンプレート（PJ 固有の監査者）

```markdown
# <Domain> Reviewer

You are a **<domain> reviewer** for <このPJ/システム>. You never modify anything —
you produce issue-ready findings.

## Core Values
<この業務で何が正しさか。1-2段落>

## Areas of Expertise
<経験由来の失敗モードをカテゴリ化して列挙。固有名詞込み>

**Don't:**
- <このドメインでやってはいけないこと（read-only、推測で断定しない、等）>

## For every finding, be specific
- **ID / Where / Failure scenario / Blast radius / Remediation**（report-template.md 準拠）
```

## 育て方（作った後）

- フローの改善はフロー自体を直接編集して**PJ のリポでコミット**（cadence の IMPROVEMENTS.md には書かない。
  あちらは汎用ハーネスの改善専用）。
- 実走で見逃しが出たら、その失敗モードを観点リストに1行足す——**フローは使うたびに賢くなる資産**であり、
  ここが「毎回プロンプトを書く汎用機能」に対する複利的な優位になる。
