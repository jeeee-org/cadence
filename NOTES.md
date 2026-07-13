# NOTES

## Codex対応の設計判断

- 既存の `claude-rules` / `quorum` と現行PCで実動している契約に合わせ、初期のCodex配置先は `$CODEX_HOME/skills/cadence` とする。公式推奨の `$HOME/.agents/skills` への移行は3リポを揃えて別途行う。
- `skills/cadence/` を共有資産の正本とし、Codex版はインストール時に `skills/codex-cadence/SKILL.md` と `agents/` を上書きして自己完結した配置物を組み立てる。
- ドメインフローはホスト横断で共有できる `<PJ>/.agents/cadence/` を新しい正本とし、既存資産を壊さないため `<PJ>/.claude/cadence/` を次順位で解決する。
- フロー内の `Read` / `Glob` / `Grep` / `Bash` / `Edit` / `Write` / `Task` は能力ラベルとして残し、Codex版SKILLで実際のツールへ写像する。汎用フローをホスト別に複製しない。
- Codexの `PreToolUse` deny形式は既存hookと互換だが、`apply_patch` は対象パスを `tool_input.command` 内に持つため、patch headerを保守的に解析する。解析不能時はセンチネル存在中だけfail closedにする。
- hookの相対パス判定は実際の書込みと同じhook入力`cwd`を基準にし、run rootは境界判定にだけ使う。許可先は`.cadence/runs/`に限定し、`.cadence/readonly`はstructured editorから変更できない制御状態とする。
- センチネルは開始・終了境界のshell制御操作で管理し、最終state確定後だけ撤去する。これは全shell経路を守れない既知制約を解消するものではなく、structured `apply_patch`による自己解除を閉じるための責務分離。
- Codexの非managed command hookは登録だけでは実行されず、`/hooks`でexact definitionのreview/trustが必要。command変更時は再trustする。
- readonly guardはsession cwdの祖先を最初のGitルートまでだけ探索する。外部targetやouter repoのsentinelをnested Gitリポへ継承しないのはfail-openの既知境界なので、対象rootからホストを開始し、stateへhook確認状態を明示する。
- non-empty `$CODEX_HOME/AGENTS.override.md`は同階層の`AGENTS.md`を隠す。installerはoverrideを勝手に編集せず、管理ブロックが不活性になることと手動統合先を警告する。
- root `AGENTS.md`のmain直接編集・自動push許可は、owner管理の低リスク個人リポとして意図したPJ方針。認証権限自体は付与しない。共有保守へ移行する時は見直す。
- Codex hookは一部shell経路の遮断が不完全なので、read-onlyの第一境界は引き続き参照専用MCP・read-only資格情報・書き込めない環境とする。
- 並列監査は領域内の深さには効くが、runbookとalertのような領域横断不変条件を暗黙には拾えない。横断要件は「全項目を列挙する対応表」としてplan/audit/superviseの三段に明記する。
