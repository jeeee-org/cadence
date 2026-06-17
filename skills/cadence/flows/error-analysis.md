# flow: error-analysis

```yaml
purpose: >
  エラー/インシデントの根本原因分析（read-only）。症状・ログ・関連コードを整理し、
  原因候補を複数立て、各候補を証拠（ログ/メトリクス/コード機構/可能なら再現）で
  確認・反証する。第一候補へのアンカリングを避け、確証の取れた根本原因（or 確信度つき
  候補集合）と修正案を issue-ready なレポートにまとめる。何も変更しない。
mode: read-only
initial: plan
max_cycles: 3          # supervise ↔ review の上限。超えても確証が進まなければ ABORT（最善仮説を確信度つきで報告）
```

## steps

### plan
- **persona**: planner
- **tools**: Read, Glob, Grep, Bash(参照系), WebSearch, WebFetch
- **edit**: no
- **instruction**:
  - 症状を確定：エラーメッセージ/スタックトレース、発生時刻と頻度、影響範囲（どのサービス/ユーザー/環境）、再現条件の有無。
  - 調査サーフェスを列挙：関係しそうなコードパス（モジュール/関数）・設定・依存。**どの runbook/コードを読むか**を具体名で。
  - 突き合わせるライブ信号を洗い出す（MCP）：onset 前後のデプロイ/設定変更、ログ・メトリクス、直近インシデント、リソース逼迫。
  - 収集すべき証拠と、各原因候補の**確認方法（できれば再現/決定論チェック）**の当たりをつける。
- **next**:
  - 症状とサーフェスが切れて調査計画が立つ → `investigate`
  - 症状/情報が不足し原因の見当もつけられない → `ABORT`（何が足りないか明示）

### investigate
- **persona**: rca-analyst
- **tools**: Read, Glob, Grep, Bash(参照系), WebSearch, WebFetch
- **edit**: no
- **parallel**: 3        # 複数サブシステム/複数仮説を分担調査（各サブエージェントにも read-only と出力様式を明示）
- **mcp**: infra         # ライブ信号取得。⚠️ read-only MCP のみ／資格情報も read-only（SKILL.md「read-only の担保方針」）
- **instruction**:
  - タイムライン再構成：onset 時刻を特定し、直前の変更（デプロイ/設定/トラフィック/依存障害）と並べる。
  - 実装の機構を確認：関係コードを `file:line` で読み、症状を生む経路を特定（相関だけで断定しない）。
  - **原因候補を複数列挙**。各候補に〔支持する証拠（ログ/`file:line`/メトリクス/イベント）〕〔反証〕〔確認方法（再現コマンド/失敗する検査が理想、無ければ相関＋機構）〕〔現時点の確信度〕。
  - 症状 / 近接原因 / 根本原因 / 寄与要因 を層として区別する。
- **next**:
  - 候補列挙と一次証拠が揃った → `verify`

### verify
- **persona**: rca-analyst
- **tools**: Read, Glob, Grep, Bash(参照系・再現用), WebSearch, WebFetch
- **edit**: no
- **mcp**: infra
- **instruction**:
  - 各候補を**確認/反証**する。最優先は**再現**：再現コマンド/スクリプトがあれば実行（**非ミューテーション・安全/非本番環境のみ**）。無ければ最強の相関＋機構で裏取り。
  - 反証も能動的に試す（本命だけ確認しない）。ライブ突合（MCP）でドキュメント上の前提と実態の乖離も確認。
  - 候補を確信度で順位づけし、**ruled out（除外）した候補と理由**を残す。
- **next**:
  - 根本原因が確証 or 候補が確信度つきで整理できた → `supervise`

### supervise
- **persona**: supervisor
- **tools**: Read, Glob, Grep, Bash(参照系)
- **edit**: no
- **judge(任意)**: **根本原因が割れる/高ステークス**な時は quorum に外注（証拠を絞って渡し、独立 RCA の合意・矛盾・盲点で裏取り）。
- **instruction**:
  - 完成度を判定：①候補を**網羅**したか（有力な代替を見落としていないか）②結論が **issue-ready**（根本原因＋証拠チェーン＋確認方法＋影響範囲＋修正案）か ③確信度は証拠に見合うか。
  - 未確認の有力候補・欠けている証拠・未試行の再現があれば特定する。
- **next**:
  - 根本原因が十分な証拠で確証され issue-ready → `COMPLETE`
  - 有力候補が未確認 or 証拠不足だが、あと1サイクルで詰まりそう → `review`
  - サイクル上限に達し確証が進まない → `ABORT`（最善候補を**確信度と残る不確実性つき**で正直に報告）

### review
- **persona**: rca-analyst
- **tools**: Read, Glob, Grep, Bash(参照系・再現用)
- **edit**: no
- **mcp**: infra
- **instruction**:
  - supervisor が指摘したギャップ（未確認候補・欠落証拠・未試行の再現）を埋める。read-only。investigate/verify と同じ候補フォーマット。
- **next**:
  - 追加検証が済んだ → `supervise`

## convergence
`supervise ↔ review` を `max_cycles`(=3) まで回す。上限に達しても確証が進まない（同じ候補で堂々巡り・
新しい証拠が出ない）なら **ABORT し、最善仮説を確信度・残る不確実性・次に取るべき証拠とともに正直に出す**。
「証拠が増えている／候補が絞れている」間だけ継続する。

## gates（任意・決定論）
根本原因の**再現が決定論化**できたら有効化する（`references/gates.md`）。
例：再現スクリプトが「バグを再現したら exit 0」を返すなら、確認の決定論アンカーになる。
再現できない（非ゼロ）＝その候補は未確証 → `review` に戻す。

```yaml
gates:
  - name: repro-confirms-root-cause
    command: ./scripts/repro.sh        # 例：当該条件で症状を再現したら exit 0
    timeout_sec: 180
    on_fail: review
```

> 修正の**適用**はこのフローの範囲外（read-only）。修正に進む場合は出力（修正案）を入力に
> `fix-reliability`（`mode: edit`・有人承認）へ渡す。
