# HANDOFF — cadence v0.3 の実MCP検証（MCP 接続済みのPCで）

cadence はClaude Code / Codex両ホストの合成フィクスチャ実走まで完了している（このリポ＝`jeeee-org/cadence`、PUBLIC）。
**残作業は「実際に cadence を一度通して詰まりを潰す」こと**で、それには
**ライブ状態を引ける infra MCP がつながった PC**で作業する必要がある。その引き継ぎメモ。

## ゴール
`audit-reliability <対象>` をClaude CodeまたはCodexで実走し、plan→audit→supervise→review が
意図通り回るか／read-only が守られるか／MCP ドリフト検出が効くか を確認する。

## 0. 前提
- そのPCにClaude CodeまたはCodexが入っている。
- **read-only の infra MCP**（kubernetes参照、クラウドのread系など）をホストに設定済み、または設定できる。

## 1. 取得 & インストール
```bash
git clone https://github.com/jeeee-org/cadence
cd cadence
./install.sh          # ~/.claude と $CODEX_HOME の両方へ配置
# Claude Codeは再起動 or /reload-skills。Codexは反映されなければ再起動
```

## 2. MCP の接続（重要：cadence は MCP を“自前で”起動しない）
- cadence は**スキル**なので、MCP は**ホストのMCP設定**から提供される。
  フロー定義の `mcp: infra` は「infra という MCP のツールを使え」という**ラベル**にすぎない（TAKT のように
  workflow 内に MCP サーバ定義を埋め込むのとは違う）。
- 手順：
  1. 実走するホストにread-onlyのinfra MCPを1つ設定する。
  2. そのサーバ名を確認し、`skills/cadence/flows/audit-reliability.md` の `mcp: infra` を**その名前に合わせる**
     （または MCP 側を `infra` という名前で登録する）。
- 🔒 **read-only は MCP/権限で物理的に固める**（指示遵守だけに頼らない／SKILL.md「read-only の担保方針」）：
  1. 繋ぐ MCP は**参照系のみ**。書き込み系ツールを持つ MCP はそもそも繋がない。
  2. MCP/CLI の**資格情報を read-only に絞る**（参照のみの k8s ServiceAccount、read 権限だけの IAM 等）。万一の書き込み試行を権限側で弾く。
  3. 可能なら本番に書き込めない環境/ネットワークで回す。
  - メインセッションは Edit/Write を持つため、「書くな」という指示は補助層にすぎない。上の 1〜3 を先に固めること。
  4. （opt-in）**ローカルファイルへの書き込みは readonly-guard hook で deny** できる。install.sh が
     表示する設定をClaude CodeのsettingsまたはCodexのhooksへ追記すると、ラン中（`./.cadence/readonly` 存在中）の
     Edit/Write/NotebookEdit/apply_patchがブロックされる（`skills/cadence/hooks/readonly-guard.py`）。
     Codexではshell書込みの全経路を遮断しないため、上の1〜3を必須とする。

## 3. 実走
```bash
/cadence audit-reliability <監査対象パス（例: ./infra や runbook ディレクトリ）>
# Codex: $cadence を使って audit-reliability で <監査対象パス> を監査して
```
- read-only 監査が plan→audit→supervise→review で回り、`.cadence/runs/<id>/` に各 step のレポート、
  最後に issue-ready な総合レポート（場所／故障シナリオ／影響範囲／修正案）が出る。

## 4. 検証チェックリスト

**2026-07-06 に `fixtures/`（合成フィクスチャ＋擬似ライブ状態）で実走検証済み**。infra MCP なしで
検証できる項目は潰した。結果の詳細は当日の `.cadence/runs/2026-07-06-fixture-01/`（05-scoring 参照。
仕込んだ欠陥 13/13 検出・偽陽性 0・ドリフト系全件検出）。

- [x] フロー定義とペルソナを正しく読み込み、ステートマシン通り遷移するか（plan→audit(並列2)→supervise→COMPLETE→fuse を確認）
- [x] **read-only が守られるか**（サブエージェント含め Edit/Write 不使用。`git status` で fixtures 無変更を機械確認）
- [x] ライブ状態と runbook/IaC の**ドリフト検出**が機能するか（擬似ライブ JSON で7件検出。**実 MCP での検証は未**）
- [x] Codex版がplan→並列audit→supervise→COMPLETEを完走し、全13資料・17 findings・非`.cadence`のSHA-256不変を確認（2026-07-13）
- [ ] runbook↔alert対応表の改善後forward-test（実行時のモデル容量不足で未完。決定論契約テストは追加済み）
- [ ] supervise↔review の**収束監視**（部分的：supervise の判定は機能したが cycle 1 で COMPLETE したため review ループと ABORT は未発火。発火させるには意図的に不完全な監査を返す adversarial フィクスチャが要る→ IMPROVEMENTS.md）
- [ ] 実 infra MCP を繋いだ実走（このチェックだけ MCP 接続済み PC が必要）
- [ ] （任意）`gates` に決定論チェックを足したら exit code で分岐するか（`references/gates.md`）
- [ ] （任意）supervise で **quorum 外注**を試したら合議が噛み合うか

## 5. フィードバックの残し方
- 直したい挙動は Issue、または `SKILL.md` / `flows/*.md` / `references/personas/*.md` を直接編集 → commit。
- 改善の起点：read-only の強制が弱い／フロー書式が回しにくい／レポート様式 など気づきを README か checkpoint に。

## 6. このPCから直接 push する場合の認証
- **public なので clone（読み取り）はログイン不要**。ただし **push は認証必須**。
- このPCを自分の GitHub（`jeeee4`）で認証すれば直接 push できる：`gh auth login`（HTTPS）か SSH 鍵か PAT。
- コミットメールは **`jeeee4@users.noreply.github.com`** にする：
  ```bash
  git config user.name  "jeeee4"
  git config user.email "jeeee4@users.noreply.github.com"
  ```
  （`@msn.com` など非公開メールのままだと public への push が GitHub のメール保護で弾かれる。実際に初回そうなった。）

---

## 補足 Q&A（GitHub の権限まわり）
- **ログインしない状態でコミットできる？** — ローカルの `git commit` はログイン不要でできる（手元の作業）。
  だが GitHub のリポに反映する **`git push` は認証が必須**。匿名でできるのは public の clone / 読み取りまで。
- **無関係な人だと PR になる？** — その通り。書き込み権限の無い人（オーナーでもコラボレーターでもない）は
  直接 push できず、**fork → 自分のコピーにコミット → Pull Request** を送る形になる。
- **自分の別PCは？** — リポは `jeeee-org`（あなたの org）所有なので、そのPCを `jeeee4` で認証すれば
  **PR を介さず直接 push できる**（fork 不要）。複数PCを共用するなら同一アカウント認証で十分。
