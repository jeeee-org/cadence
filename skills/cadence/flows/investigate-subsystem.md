# flow: investigate-subsystem

```yaml
purpose: >
  特定サブシステム/モジュールの動作・構造を read-only で正確に把握する。責務・エントリポイント・
  制御/データフロー・不変条件/契約・依存と副作用・エッジケースを file:line 接地でマップし、
  正確なメンタルモデルと未解決の疑問点を出す。バグ探しでも修正でもなく「正しく理解する」ことが目的。
  何も変更しない。
mode: read-only
initial: plan
max_cycles: 3          # supervise ↔ review の上限。超えても被覆が進まなければ ABORT（マップ済み＋未踏を明示）
```

## steps

### plan
- **persona**: planner
- **tools**: Read, Glob, Grep, Bash(参照系), WebSearch, WebFetch
- **edit**: no
- **instruction**:
  - 調査対象の**境界**を確定：どのモジュール/ディレクトリ/サービスか、何を理解したいか（全体構造の把握か特定挙動の解明か）。
  - サーフェスを**具体名で列挙**：エントリポイント（公開API/ハンドラ/CLI/ジョブ/イベント）、主要ファイル、設定、依存（呼ぶ先・呼ばれる元）。
  - 理解したい**問い**を立てる：どう動くか／状態はどこで変わるか／外部とどう接するか／どんな前提・契約か。
  - 実行時挙動が構成依存（フラグ/設定/デプロイ）なら、MCP で突き合わせる対象を挙げる。
- **next**:
  - 境界とサーフェスが切れて調査計画が立つ → `investigate`
  - 対象が曖昧で絞れない・情報不足 → `ABORT`（何が足りないか明示）

### investigate
- **persona**: code-investigator
- **tools**: Read, Glob, Grep, Bash(参照系), WebSearch, WebFetch
- **edit**: no
- **parallel**: 3        # 領域/レイヤーごとに分担（各サブエージェントにも read-only と出力様式を明示）
- **mcp**: infra         # 任意。実行時の構成値の突合に使う場合のみ。⚠️ read-only MCP のみ／資格情報も read-only（SKILL.md「read-only の担保方針」）
- **instruction**:
  - 各領域を精読し **file:line 接地**でマップ：責務／エントリポイント／制御フロー（エラー・早期 return 含む）／データ・状態フロー（生成・変更・読取・永続化、共有 vs ローカル）／不変条件・契約／依存と副作用（IO・外部呼び出し）／エッジケース・失敗時挙動。
  - **全エントリポイント・呼び出し箇所を grep で網羅**。動的ディスパッチ／設定駆動分岐／リフレクション／イベントハンドラは**未解決として明示**（推測で埋めない）。
  - コードの実挙動と、コメント/ドキュメントの主張に差分があれば記す。
  - （MCP・任意）構成依存の挙動は実行時の値と突き合わせる（参照のみ）。
- **next**:
  - サーフェスのマップと未解決点が揃った → `supervise`

### supervise
- **persona**: supervisor
- **tools**: Read, Glob, Grep, Bash(参照系)
- **edit**: no
- **judge(任意)**: 解釈が割れる/重要な箇所で確信が要る時は quorum に外注（該当コードと根拠を絞って渡す）。
- **instruction**:
  - 完成度を判定：①対象サーフェスを**網羅**したか（未読の主要パス・呼び出し箇所を名指し）②理解が**具体**か（file:line 接地でハンドウェーブでない）③未解決の疑問が整理され、推測で塗りつぶしていないか。
- **next**:
  - 網羅・具体・疑問整理済み → `COMPLETE`
  - 未読パス/曖昧な箇所あり、かつあと1サイクルで埋まりそう → `review`
  - サイクル上限に達し被覆が進まない → `ABORT`（マップ済み範囲と未踏範囲を正直に明示）

### review
- **persona**: code-investigator
- **tools**: Read, Glob, Grep, Bash(参照系), WebSearch, WebFetch
- **edit**: no
- **mcp**: infra
- **instruction**:
  - supervisor が指摘したギャップ（未読パス・未網羅の呼び出し箇所・曖昧な挙動）を精読で埋める。read-only。investigate と同じマップ様式。
- **next**:
  - 追加調査が済んだ → `supervise`

## convergence
`supervise ↔ review` を `max_cycles`(=3) まで回す。上限に達しても被覆が進まない（同じ箇所の往復・
新規に読めるパスが出ない）なら **ABORT し、マップ済み範囲・未踏範囲・未解決の疑問を正直に出す**。
「読める範囲が広がっている／理解が深まっている」間だけ継続する。

## gates（任意・決定論）
メンタルモデルの**土台を機械的に確認**したい時に有効化する（`references/gates.md`）。
例：テストスイート／ビルド／型チェックを回し、「自分の理解が前提とする状態が実際に成立するか」を裏付ける。
非ゼロ（壊れている/前提が崩れる）→ `review` に戻して読み直す。

```yaml
gates:
  - name: build-and-tests-baseline
    command: <ビルド or テスト or 型チェックのコマンド>   # 例: npm test / pytest -q / tsc --noEmit
    timeout_sec: 300
    on_fail: review
```

> 出力は「**サブシステム・マップ**」（責務／エントリポイント／制御・データフロー／不変条件・契約／
> 依存・副作用／エッジケース／未解決の疑問）。バグ修正・変更は範囲外（read-only）。実装に進む場合は
> このマップを入力に通常の実装作業や `fix-reliability`（`mode: edit`・有人承認）へ渡す。
