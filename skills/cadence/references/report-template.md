# report-template — finding と最終レポートの様式

issue-ready の定義を一箇所に固める。各フローの instruction・supervise の判定・fuse の出力は
この様式を正とする（フロー側の記述はこの要約）。

## finding の様式（audit/investigate/review 系 step の出力単位）

```markdown
### <ID>: <一行タイトル>
- **場所**: file:line（ライブ由来なら どの MCP/JSON のどのフィールド）
- **故障シナリオ**: 何がトリガで何が起きるか（トリガ＋制御点を具体的に）
- **影響範囲**: 何がどこまで壊れるか（blast radius）
- **修正案**: 具体的な直し方
```

- **ID は安定**させる：`<領域>-<連番>`（例 `F-A3`）か `<file>:<短スラッグ>`。サイクルをまたいだ
  同一指摘は同じ ID を使い回す（supervise の停滞判定＝前サイクルとの ID 集合差分の前提）。
- 4項目のどれかが書けない finding は issue-ready でない（supervise は `review` に差し戻す）。
- 憶測で水増ししない：セーフガードの不在だけでは finding にせず、現実的シナリオを示せるものだけ。
- 各 step の末尾に〔監査済みファイル一覧〕〔確認したが問題なしと判断した観点〕を添える
  （被覆の証明。supervise はこれで coverage を判定する）。

## 最終レポート（fuse）の様式

```markdown
# <flow> 最終レポート: <対象> (<日付>)
対象・スコープ・結果サマリ（findings 件数、重複統合の注記）

## Critical / High / Medium（深刻度順のセクション）
（finding を上の様式で。重複は統合し [元ID] を残す）

## 監査証跡
- フロー遷移（state.md の要約：どの step を何サイクル・各 supervise の判定）
- read-only の確認方法（git status / hook）
- ライブ突合に使ったソース一覧
- 未被覆（既知ギャップ）と ABORT の場合はその理由
```

- 深刻度はデータ全損・復旧手順の実行不能 > SPOF・無検知 > 再現性・増幅 の順を目安に。
- 監査証跡は畳んでよいが省略しない（後から「なぜこの結論か」を追える状態が issue-ready の一部）。
