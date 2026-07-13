# cadence

**構造化レビューループ（plan → audit → supervise → review）を宣言的フローとして回す、自作の Claude Code / Codex ハーネス。**

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
├── install.sh                     # ~/.claude / $CODEX_HOME へ配置（配置前にフロー検証）
├── rules/
│   ├── cadence-triage.md          # Claude Code版トリアージ
│   └── codex-cadence-triage.md    # Codex版 CADENCE → $cadence 接続
├── scripts/
│   └── validate-flows.py          # フロー定義の決定論バリデータ（exit code 判定）
├── fixtures/                      # 実走検証用の合成インフラリポ（欠陥入り＋擬似ライブ状態＋正解リスト）
├── commands/
│   └── cadence.md                 # /cadence スラッシュコマンド（薄いラッパ。ルールは SKILL.md が正）
├── skills/codex-cadence/
│   ├── SKILL.md                   # Codex固有の実行手順
│   └── agents/openai.yaml         # Codex UIメタデータ
├── tests/                         # 両ホストinstall・hook・フロー解決のAPI不要テスト
└── skills/cadence/
    ├── SKILL.md                   # Claude Code版手順＋共有資産の正本
    ├── hooks/
    │   └── readonly-guard.py      # 両ホストPreToolUse：ラン中の編集をdeny（opt-in）
    ├── flows/
    │   ├── audit-reliability.md   # フロー定義（SRE read-only 信頼性監査）
    │   ├── error-analysis.md      # フロー定義（read-only RCA：原因候補→証拠で確認/反証→収束）
    │   ├── investigate-subsystem.md # フロー定義（read-only：サブシステムの動作・構造を file:line 接地でマップ）
    │   ├── optimize-context.md    # フロー定義（mode: edit・有人承認：CLAUDE/AGENTS等を意味を失わずスリム化）
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
./install.sh            # ~/.claude と $CODEX_HOME の両方へ配置
# Claude Codeは再起動 or /reload-skills。Codexは反映されなければ再起動

# Claude Code（例）
/cadence audit-reliability ./infra            # infra ディレクトリを read-only 監査
/cadence error-analysis <症状/ログ/対象パス>   # read-only で根本原因分析（RCA）
```

Codexのプロンプト例：
```text
$cadence を使って audit-reliability で ./infra を監査して
$cadence を使って error-analysis でこの障害を分析して
```
- フローの `audit` step の `mcp: infra` を自分の MCP サーバ（参照系）に合わせる。
- 新しい監査・調査タイプは `flows/<name>.md` を1枚足すだけ（SKILL.md は無改修）。
- 検証が定着したら `gates:` に決定論チェック（Bash）を足す。

### ドメインフローは各PJ側に置く（推奨構成）

cadence の強さの源泉は実行エンジンではなく、**フローに書かれたドメイン知識**（経験由来の観点リスト・
品質基準・そのPJで踏んだ失敗モード）にある。そこで：

- **cadence（このリポ・public）＝共通エンジン＋規約＋汎用フロー**。全PCに clone → install。
- **ドメインフロー＝各PJの `<PJ>/.agents/cadence/flows/`（＋`personas/`）**。PJ のリポでコミットし、
  PJ と一緒に各PCへ移動する。業務の知識・固有名詞はPJ側に閉じる（public の cadence に持ち込まない）。
- 旧 `<PJ>/.claude/cadence/` も後方互換で読める。解決順は〔`.agents` → `.claude` → 同梱〕。
- 既存PJの `NOTES.md`・checkpoints に溜まった知見をフローへ**蒸留する手順**は
  [flow-authoring.md](skills/cadence/references/flow-authoring.md)。PJ側フローの機械検証は：
  ```bash
  python3 <cadenceリポ>/scripts/validate-flows.py --project-dir <PJルート>
  ```

### 別PCでのセットアップ
各マシンで **clone → `./install.sh`** を回す。これだけで Claude Code / Codex の両方へ配置される。
```bash
git clone https://github.com/jeeee-org/cadence.git
cd cadence
./install.sh
# Claude Codeは再起動 or /reload-skills。Codexは反映されなければ再起動
```
- 新PCでは `claude-rules → quorum → cadence` の順で各 `install.sh` を実行するとグローバル指示の並びが揃う。
- Codex版の既定配置は、兄弟リポと現行環境に合わせて `$CODEX_HOME/skills/cadence`。公式推奨の `$HOME/.agents/skills` へは3リポを揃えて移行する（[REQUIREMENTS.md](REQUIREMENTS.md) の未決事項）。
- **更新を取り込む時も同じ**：`git pull` の後に `./install.sh` を再実行する（install.sh は配置先を `rm -rf` して入れ直す）。
- **改善メモ（`IMPROVEMENTS.md`）はマシンごとに symlink を張り直す**：Claude/Codex両方の配置先から、git管理下のリポroot正本を参照する。再インストールでも消えない。
- 溜まった改善メモは普通に `git add IMPROVEMENTS.md && git commit && git push` で共有し、他PCは `git pull` で受け取る。

## コアの考え方
- **read-only 既定**：監査は指摘・リスク・修正案を出すだけ。何も変更しない。
- **収束監視**：`max_cycles` は**ハードキャップ**（到達で必ず停止。「改善中だから延長」はしない）。上限前でも finding ID 集合に差分が無ければ停滞として**部分結果で ABORT**。ラン状態は `.cadence/runs/<id>/state.md` が正（再開可能）。
- **決定論ゲート**：モデルのブレは LLM 判定でなく**コマンドの exit code**で弾く（[references/gates.md](skills/cadence/references/gates.md)）。
- **高ステークス判断は quorum 外注**：確信が要る step だけ多モデル合議に回す（コスト N 倍なのでここぞに限定）。
- **使い忘れはトリアージで防ぐ**：Claude Codeはグローバル `CLAUDE.md` から提案し、Codexは `claude-rules` の `CADENCE` 分類を `$cadence` へ接続する。分類基準はcadence側で複製しない。

## 状態 / 引き継ぎ
- **v0.3**。Claude Code / Codex両ホスト対応＋**合成フィクスチャで実走検証済み**。Codex版は全13資料を被覆して17件をissue-ready化し、非`.cadence`ファイルのSHA-256不変も確認した。初回実走で判明した領域横断の見逃しは、runbook↔alert対応表をplan/audit/superviseへ追加して決定論テストで固定した。`/cadence audit-reliability fixtures/target` または `$cadence` で再検証できる（infra MCP不要）。
- 改善後のfresh forward-testは実行時のモデル容量不足で未完。API不要テスト15件とskill validatorは通過済み。
- 残検証：**実 infra MCP を繋いだ実走**・supervise↔review ループの発火・gates/quorum の実地。
  引き継ぎ手順は [HANDOFF.md](HANDOFF.md)（§4 のチェックリストに済/未を反映済み）。

## 注意・限界
- **read-only は指示遵守だけでは弱い**。**MCP/権限で物理的に固める**のが本筋：参照系MCPのみ接続／資格情報をread-onlyに絞る／触れない環境で回す。ローカル編集は両ホスト対応readonly-guard hook（opt-in）で補助できるが、Codexではshell書込みの全経路を遮断する境界とはみなさない。
- ペルソナ/フローはテキスト指示であり実行系の強制ではない。step ごとに自己点検する。
- cadence は MCP を自前で起動しない。**ホストのMCP設定**を使い、フローの `mcp:` は能力ラベル（[HANDOFF.md](HANDOFF.md) §2）。
