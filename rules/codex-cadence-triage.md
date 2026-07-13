## Codex版 cadence 連携

- `claude-rules` の分類で **CADENCE** となり、ユーザーが実行まで求めている場合は、利用可能な `$cadence` で対応フローを実行する。提案だけで作業を止めない。
- ユーザーが「cadenceで」「$cadence」と明示した場合は分類より優先して `$cadence` を使う。
- T0 / T1 / T2a では cadence を自動使用しない。T1は利用可能なら `$quorum`、T2aはメインCodexの単独深掘りへ渡す。
- PJ固有フローは `.agents/cadence/flows/`、後方互換の `.claude/cadence/flows/`、同梱フローの順に解決する。
- 分類基準はここで再定義しない。正本は `claude-rules` が配置する `triage-rubric.txt` とする。
