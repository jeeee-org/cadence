# NOTES

## Codex対応の設計判断

- 既存の `claude-rules` / `quorum` と現行PCで実動している契約に合わせ、初期のCodex配置先は `$CODEX_HOME/skills/cadence` とする。公式推奨の `$HOME/.agents/skills` への移行は3リポを揃えて別途行う。
- `skills/cadence/` を共有資産の正本とし、Codex版はインストール時に `skills/codex-cadence/SKILL.md` と `agents/` を上書きして自己完結した配置物を組み立てる。
- ドメインフローはホスト横断で共有できる `<PJ>/.agents/cadence/` を新しい正本とし、既存資産を壊さないため `<PJ>/.claude/cadence/` を次順位で解決する。
- フロー内の `Read` / `Glob` / `Grep` / `Bash` / `Edit` / `Write` / `Task` は能力ラベルとして残し、Codex版SKILLで実際のツールへ写像する。汎用フローをホスト別に複製しない。
- Codexの `PreToolUse` deny形式は既存hookと互換だが、`apply_patch` は対象パスを `tool_input.command` 内に持つため、patch headerを保守的に解析する。解析不能時はセンチネル存在中だけfail closedにする。
- Codex hookは一部shell経路の遮断が不完全なので、read-onlyの第一境界は引き続き参照専用MCP・read-only資格情報・書き込めない環境とする。
- 並列監査は領域内の深さには効くが、runbookとalertのような領域横断不変条件を暗黙には拾えない。横断要件は「全項目を列挙する対応表」としてplan/audit/superviseの三段に明記する。
