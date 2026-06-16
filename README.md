# cadence

**構造化レビューループ（plan → audit → supervise → review）を宣言的フローとして回す、自作の Claude Code ハーネス。**

TAKT の思想（AI の自律に委ねず、外側から構造で律する）を**参考にしつつ独立実装**したもので、
TAKT には依存しない（npm も不要）。エンジンはメインの Opus 4.8 セッションそのもの——フロー定義と
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
├── install.sh                     # ~/.claude へ配置
├── commands/
│   └── cadence.md                 # /cadence スラッシュコマンド
└── skills/cadence/
    ├── SKILL.md                   # エンジン（メイン Opus への実行手順）
    ├── flows/
    │   └── audit-reliability.md   # フロー定義（SRE read-only 信頼性監査）
    └── references/
        ├── gates.md               # 決定論ゲート（Bash の exit code で機械判定）
        └── personas/
            ├── planner.md         # スコープ設計
            ├── sre-reviewer.md    # 信頼性監査（read-only）
            └── supervisor.md      # 収束判定（COMPLETE/review/ABORT）
```

## 使い方
```bash
./install.sh            # ~/.claude/skills/cadence と commands/cadence.md を配置
# Claude Code を再起動 or /reload-skills

# 実行（例）
/cadence audit-reliability ./infra            # infra ディレクトリを read-only 監査
```
- フローの `audit` step の `mcp: infra` を自分の MCP サーバ（参照系）に合わせる。
- 新しい監査・調査タイプは `flows/<name>.md` を1枚足すだけ（SKILL.md は無改修）。
- 検証が定着したら `gates:` に決定論チェック（Bash）を足す。

## コアの考え方
- **read-only 既定**：監査は指摘・リスク・修正案を出すだけ。何も変更しない。
- **収束監視**：`max_cycles` で supervise↔review を打ち切り、改善が止まれば**部分結果で ABORT**（無限ループにしない）。
- **決定論ゲート**：モデルのブレは LLM 判定でなく**コマンドの exit code**で弾く（[references/gates.md](skills/cadence/references/gates.md)）。
- **高ステークス判断は quorum 外注**：確信が要る step だけ多モデル合議に回す（コスト N 倍なのでここぞに限定）。

## 状態 / 引き継ぎ
- **v0 雛形**。構造は一通り完成、`~/.claude` 配置・スキル登録まで確認済み。**実走検証は未**。
- 実走には **infra MCP がつながった PC** が要る。その引き継ぎ手順は [HANDOFF.md](HANDOFF.md)
  （インストール・MCP 接続・実走・検証チェックリスト・push 認証の注意）。

## 注意・限界
- read-only はメイン権限（Edit/Write あり）では**運用規律で担保**。ライブに触る MCP は参照系のみに。
- ペルソナ/フローはテキスト指示であり実行系の強制ではない。step ごとに自己点検する。
- cadence は MCP を自前で起動しない。**ホスト Claude Code の MCP 設定**を使い、フローの `mcp:` はラベル（[HANDOFF.md](HANDOFF.md) §2）。
