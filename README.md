# cadence

**構造化レビューループ（plan → audit → supervise → review）を宣言的フローとして回す、自作の Claude Code ハーネス。**

TAKT の思想（AI の自律に委ねず、外側から構造で律する）を**参考にしつつ独立実装**したもので、
TAKT には依存しない（npm も不要）。エンジンはメインセッションそのもの（モデル非依存）——フロー定義と
ペルソナを読み、各 step を実行し、収束を見張りながら遷移する。read-only な監査・調査、特に
SRE 的な「巨大MD（runbook/IaC/設定）＋ライブ状態の欠陥発見→検証」に向く。

## なぜ作ったか
- **判断中心の環境**（実装が主でない／巨大 MD ／retrieval が skill・MCP 化済み）では、
  「計画→監査→監督→再監査」を**反復ループで詰める**ハーネスが噛み合う。
- 既存ツール（TAKT）はコーディングの計画→実装→レビュー→修正に最適化。こちらは
  **read-only 監査**を一級市民に据え、ライブ状態（MCP）との**ドリフト検出**を組み込んだ。
- 相棒スキル [quorum](https://github.com/jeeee-org/quorum)（多モデルの合議で重要判断を裏取り）と
  **合成**できる：cadence＝指揮者（手順を回す）、quorum＝専門家会議（ここぞの判断）。

## 構成
```
cadence/
├── install.sh                     # ~/.claude へ配置（配置前にフロー検証・CLAUDE.md にトリアージ注入）
├── rules/
│   └── cadence-triage.md          # グローバル CLAUDE.md へ注入する「cadence を提案する」判定ルール（正本）
├── scripts/
│   └── validate-flows.py          # フロー定義の決定論バリデータ（exit code 判定）
├── fixtures/                      # 実走検証用の合成インフラリポ（欠陥入り＋擬似ライブ状態＋正解リスト）
├── commands/
│   └── cadence.md                 # /cadence スラッシュコマンド（薄いラッパ。ルールは SKILL.md が正）
└── skills/cadence/
    ├── SKILL.md                   # エンジン（メインセッションへの実行手順）
    ├── hooks/
    │   └── readonly-guard.py      # PreToolUse hook：ラン中の Edit/Write を deny（opt-in）
    ├── flows/
    │   ├── audit-reliability.md   # フロー定義（SRE read-only 信頼性監査）
    │   ├── error-analysis.md      # フロー定義（read-only RCA：原因候補→証拠で確認/反証→収束）
    │   ├── investigate-subsystem.md # フロー定義（read-only：サブシステムの動作・構造を file:line 接地でマップ）
    │   ├── optimize-context.md    # フロー定義（mode: edit・有人承認：CLAUDE等の肥大をルールを失わずスリム化）
    │   └── fix-reliability.md     # フロー定義（mode: edit・有人承認で issue を修正）
    └── references/
        ├── gates.md               # 決定論ゲート（Bash の exit code で機械判定）
        ├── report-template.md     # finding／最終レポートの様式（issue-ready の定義の正本）
        ├── flow-authoring.md      # ドメインフローの作り方（PJ の蓄積知識をフローに蒸留する手順）
        └── personas/
            ├── planner.md         # スコープ設計
            ├── sre-reviewer.md    # 信頼性監査（read-only）
            ├── rca-analyst.md     # 根本原因分析（read-only・複数仮説/証拠主義/反アンカリング）
            ├── code-investigator.md # コード調査（read-only・file:line 接地/全パス網羅/推測しない）
            ├── context-optimizer.md # コンテキスト最適化（mode: edit・cut bytes not meaning/ルール保全/承認制）
            ├── sre-fixer.md       # 信頼性修正（mode: edit・最小/可逆/承認制）
            └── supervisor.md      # 収束判定（COMPLETE/review/ABORT）
```

## 使い方
```bash
./install.sh            # ~/.claude/skills/cadence と commands/cadence.md を配置
# Claude Code を再起動 or /reload-skills

# 実行（例）
/cadence audit-reliability ./infra            # infra ディレクトリを read-only 監査
/cadence error-analysis <症状/ログ/対象パス>   # read-only で根本原因分析（RCA）
/cadence investigate-subsystem <モジュール/対象パス>   # read-only でサブシステムの動作・構造を把握
/cadence optimize-context <対象PJパス>                 # mode: edit でコンテキスト肥大をスリム化（承認制）
/cadence fix-reliability <audit/RCA のレポート or issue>   # mode: edit で修正（適用前に人が承認）
```
- フローの `audit` step の `mcp: infra` を自分の MCP サーバ（参照系）に合わせる。
- 新しい監査・調査タイプは `flows/<name>.md` を1枚足すだけ（SKILL.md は無改修）。
- 検証が定着したら `gates:` に決定論チェック（Bash）を足す。

### ドメインフローは各PJ側に置く（推奨構成）

cadence の強さの源泉は実行エンジンではなく、**フローに書かれたドメイン知識**（経験由来の観点リスト・
品質基準・そのPJで踏んだ失敗モード）にある。そこで：

- **cadence（このリポ・public）＝共通エンジン＋規約＋汎用フロー**。全PCに clone → install。
- **ドメインフロー＝各PJの `<PJ>/.claude/cadence/flows/`（＋`personas/`）**。PJ のリポでコミットし、
  PJ と一緒に各PCへ移動する。業務の知識・固有名詞はPJ側に閉じる（public の cadence に持ち込まない）。
- エンジンはフロー/ペルソナを〔PJ ローカル → 同梱〕の順で解決する（同名は PJ 側が勝つ）。
- 既存PJの `NOTES.md`・checkpoints に溜まった知見をフローへ**蒸留する手順**は
  [flow-authoring.md](skills/cadence/references/flow-authoring.md)。PJ側フローの機械検証は：
  ```bash
  python3 <cadenceリポ>/scripts/validate-flows.py --project-dir <PJルート>
  ```

### 別PCでのセットアップ
各マシンで **clone → `./install.sh`** を回す。これだけで `~/.claude` への配置が済む。
```bash
git clone https://github.com/jeeee-org/cadence.git
cd cadence
./install.sh
# Claude Code を再起動 or /reload-skills
```
- **更新を取り込む時も同じ**：`git pull` の後に `./install.sh` を再実行する（install.sh は配置先を `rm -rf` して入れ直す）。
- **改善メモ（`IMPROVEMENTS.md`）はマシンごとに symlink を張り直す**：正本はリポ root の `IMPROVEMENTS.md`（git 管理）で、install.sh が `~/.claude/skills/cadence/IMPROVEMENTS.md` をそのマシンのリポパスへの symlink にする。だから実行時の追記は git 管理下の正本へ書き込まれ、再インストールの `rm -rf` でも消えない。symlink 自体はリポの絶対パスを指すマシン固有のものなので、**コミットには含まれず、各PCで install.sh が張り直す**。
- 溜まった改善メモは普通に `git add IMPROVEMENTS.md && git commit && git push` で共有し、他PCは `git pull` で受け取る。

## コアの考え方
- **read-only 既定**：監査は指摘・リスク・修正案を出すだけ。何も変更しない。
- **収束監視**：`max_cycles` は**ハードキャップ**（到達で必ず停止。「改善中だから延長」はしない）。上限前でも finding ID 集合に差分が無ければ停滞として**部分結果で ABORT**。ラン状態は `.cadence/runs/<id>/state.md` が正（再開可能）。
- **決定論ゲート**：モデルのブレは LLM 判定でなく**コマンドの exit code**で弾く（[references/gates.md](skills/cadence/references/gates.md)）。
- **高ステークス判断は quorum 外注**：確信が要る step だけ多モデル合議に回す（コスト N 倍なのでここぞに限定）。
- **使い忘れはトリアージで防ぐ**：install.sh がグローバル CLAUDE.md に判定ルール（`rules/cadence-triage.md`）を注入し、条件（完成の定義が言える・関与が承認で足りる・被覆型）に合う依頼では **Claude 側から「/cadence で回しますか？」と提案**する。ユーザーが覚えておく必要はない。

## 状態 / 引き継ぎ
- **v0.1**。構造完成＋**合成フィクスチャで実走検証済み**（2026-07-06、`fixtures/` 参照：仕込んだ欠陥
  13/13 検出・偽陽性 0・擬似ライブとのドリフト検出も全件機能）。`/cadence audit-reliability fixtures/target`
  で誰でも再検証できる（infra MCP 不要）。
- 残検証：**実 infra MCP を繋いだ実走**・supervise↔review ループの発火・gates/quorum の実地。
  引き継ぎ手順は [HANDOFF.md](HANDOFF.md)（§4 のチェックリストに済/未を反映済み）。

## 注意・限界
- **read-only は指示遵守だけでは弱い**（メインは Edit/Write を持つ）。**MCP/権限で物理的に固める**のが本筋：参照系 MCP のみ接続／資格情報を read-only に絞る／触れない環境で回す。さらに**ローカルファイルは readonly-guard hook（opt-in）でハーネス側から deny** できる——ラン中のセンチネル `./.cadence/readonly` 存在中は Edit/Write をブロック（詳細は [SKILL.md「read-only の担保方針」](skills/cadence/SKILL.md) と `skills/cadence/hooks/readonly-guard.py`）。
- ペルソナ/フローはテキスト指示であり実行系の強制ではない。step ごとに自己点検する。
- cadence は MCP を自前で起動しない。**ホスト Claude Code の MCP 設定**を使い、フローの `mcp:` はラベル（[HANDOFF.md](HANDOFF.md) §2）。
