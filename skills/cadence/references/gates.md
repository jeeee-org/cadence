# gates — 決定論ゲート（Bash コマンドによる機械判定）

cadence の **ゲート**は、LLM 判定ではなく**シェルコマンドの exit code で合否を機械判定**する層。
モデルのブレ（非決定性・ドリフト）を吸収する核は、この決定論チェックにある
（テスト／lint／ポリシーチェック／スキーマ検証など）。フロー/step の `gates:` で宣言する。

## いつ使うか
- 監査・調査が定着し、「**毎回必ず満たすべき不変条件**」が固まった時。
- read-only 監査でも、生成したチェックスクリプトやポリシー検査を回して結論を裏付けられる。
- 逆に、固まっていない探索段階では無理に足さない（セットアップ代の先払いになる）。

## 書式
```yaml
gates:
  - name: <gate 名>
    command: <Bash コマンド>      # 対象リポの作業ディレクトリで実行
    timeout_sec: 120              # 任意。打ち切り秒
    on_fail: review              # 非ゼロ時の遷移先（既定 review）。COMPLETE/ABORT も可
```

## 実行規約（メイン Opus）
1. `command` を Bash で実行する。**参照・検査系のみ**（環境を変更しない）。`timeout_sec` があれば `timeout` で打ち切る。
2. **exit code で判定**：0＝合格、非ゼロ＝不合格。出力（stdout/stderr）はゲート結果として `NN-gate-<name>.md` に残す。
3. 不合格なら `on_fail` の step へ遷移（多くは `review`）。複数ゲートは**全て合格**で先へ。
4. ゲートはあくまで決定論層。LLM 判定が要る条件は step の instruction 側に書く（両者を混同しない）。

## 例（信頼性ポリシーチェック）
```bash
# ./scripts/reliability-policy-check.sh の例（雛形）
#   - 全 P1 runbook に rollback セクションがあるか
#   - terraform fmt -check / validate が通るか
#   - アラート定義に必須ラベル(severity/runbook_url)が付いているか
# いずれか欠ければ非ゼロで終了 → cadence は review に戻す
```

> 設計メモ：これは TAKT の `quality_gates`（`type: command` の決定論ゲート）に相当する概念を、
> cadence 用に独立実装したもの。TAKT ビルトインが多くは「文字列＝LLM 判定」ゲートを使うのに対し、
> cadence のゲートは**最初から exit code の決定論判定**に振っている（LLM 判定が要るなら instruction へ）。
