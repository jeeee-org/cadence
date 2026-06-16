# HANDOFF — cadence v0 の実走検証（MCP 接続済みの PC で）

cadence は v0 雛形までできている（このリポ＝`jeeee-org/cadence`、PUBLIC）。
**残作業は「実際に `/cadence` を一度通して詰まりを潰す」こと**で、それには
**ライブ状態を引ける infra MCP がつながった PC**で作業する必要がある。その引き継ぎメモ。

## ゴール
`/cadence audit-reliability <対象>` を実走し、plan→audit→supervise→review が
意図通り回るか／read-only が守られるか／MCP ドリフト検出が効くか を確認する。

## 0. 前提
- その PC に Claude Code が入っている。
- **read-only の infra MCP**（kubernetes 参照、クラウドの read 系など）を Claude Code に設定済み、または設定できる。

## 1. 取得 & インストール
```bash
git clone https://github.com/jeeee-org/cadence
cd cadence
./install.sh          # ~/.claude/skills/cadence と commands/cadence.md を配置
# Claude Code を再起動 or /reload-skills
```

## 2. MCP の接続（重要：cadence は MCP を“自前で”起動しない）
- cadence は**スキル**なので、MCP は**ホストの Claude Code の MCP 設定**（`.mcp.json` / settings）から提供される。
  フロー定義の `mcp: infra` は「infra という MCP のツールを使え」という**ラベル**にすぎない（TAKT のように
  workflow 内に MCP サーバ定義を埋め込むのとは違う）。
- 手順：
  1. Claude Code に read-only の infra MCP を1つ設定する。
  2. そのサーバ名を確認し、`skills/cadence/flows/audit-reliability.md` の `mcp: infra` を**その名前に合わせる**
     （または MCP 側を `infra` という名前で登録する）。
- ⚠️ ライブ環境に**書き込む** MCP は使わない。参照系のみ。

## 3. 実走
```bash
/cadence audit-reliability <監査対象パス（例: ./infra や runbook ディレクトリ）>
```
- read-only 監査が plan→audit→supervise→review で回り、`.cadence/runs/<id>/` に各 step のレポート、
  最後に issue-ready な総合レポート（場所／故障シナリオ／影響範囲／修正案）が出る。

## 4. 検証チェックリスト（v0 で見たいこと）
- [ ] フロー定義とペルソナを正しく読み込み、ステートマシン通り遷移するか
- [ ] **read-only が守られるか**（Edit/Write/破壊的コマンドを使っていないか）
- [ ] MCP のライブ状態と runbook/IaC の**ドリフト検出**が機能するか
- [ ] supervise↔review の**収束監視**が効くか（`max_cycles` で止まる／ABORT 時に部分結果を出す）
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
