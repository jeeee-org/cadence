<!-- cadence-triage:begin (cadence/install.sh が管理。手動編集しない — 変更はリポの rules/cadence-triage.md へ) -->
## cadence トリアージ（常時考慮）

作業依頼を受けたら、次の3条件に**全部**当てはまるか確認する：
①完成の定義を事前に1文で言える（被覆＋issue-ready 等）②途中の人間の関与が「承認/却下」に還元できる（方向づけの対話が不要）③被覆型の監査・調査・定型修正である（同型で繰り返す仕事なら特に）。

全部当てはまれば、着手前に「**/cadence <flow> で回しますか？**」と提案する（勝手に開始しない。単発・対話的/探索的な作業では不要）。候補は同梱5種に加え、**対象PJの `.agents/cadence/flows/` → `.claude/cadence/flows/` を必ず確認**する（PJ固有を優先）。ユーザーの明示指定（「cadenceで」「普通にやって」）は判定より優先する。
<!-- cadence-triage:end -->
