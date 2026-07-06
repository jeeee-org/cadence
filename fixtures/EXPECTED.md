# EXPECTED — 仕込んだ欠陥の正解リスト（採点用）

⚠️ **監査エージェントはこのファイルを読まないこと**（採点者＝人間用）。

| ID | 種別 | 場所 | 内容 |
|---|---|---|---|
| D01 | SPOF | `target/k8s/payment-deployment.yaml` | `replicas: 1` — 決済サービスが単一 Pod |
| D02 | 無制限リソース | `target/k8s/payment-deployment.yaml` | resources requests/limits が無い |
| D03 | 非再現デプロイ | `target/k8s/payment-deployment.yaml` | image が `:latest` タグ（ロールバック不能） |
| D04 | runbook 乖離 | `target/runbooks/payment-outage.md` × `live-state/deployments.json` | runbook はデプロイ名 `payments-v1`・3レプリカ前提だが、ライブは `payment-svc`・1レプリカ。INC-0042 でも手順失敗の記録あり |
| D05 | runbook 乖離 | `target/runbooks/db-failover.md` × `live-state/instances.json` | フェイルオーバー先 `db-standby-01` は廃止済みでライブに存在しない |
| D06 | rollback 欠落 | `target/runbooks/db-failover.md` | P1 runbook なのに rollback / 検証手順のセクションが無い |
| D07 | アラート/SLO 欠落 | `target/alerts/alerts.yaml` | payment サービスのアラート・SLO が一切無い（api のみ） |
| D08 | アラート誤設定 | `target/alerts/alerts.yaml` (HighErrorRate) | 閾値 `> 0.9`（エラー率90%でしか発火しない）＋ `runbook_url` ラベル欠落 |
| D09 | ライブドリフト | `target/alerts/alerts.yaml` × `live-state/alert-rules.json` | `DiskPressure` アラートが定義上は有効だがライブでは disabled |
| D10 | 容量逼迫 | `live-state/quotas.json` | `payments` namespace のメモリクォータ使用率 92%（余裕なし） |
| D11 | 単一AZ/バックアップ無 | `target/terraform/rds.tf` | `multi_az = false` かつ `backup_retention_period = 0` |
| D12 | リトライストーム | `target/k8s/api-client-config.yaml` | `retries: 10`・`backoff: none`・jitter 無し（依存障害時に thundering herd） |
| D13 | イメージドリフト | `target/k8s/api-deployment.yaml` × `live-state/deployments.json` | マニフェストは `api:v2.3.0`、ライブは `api:v2.3.1`（IaC 外の変更） |
| D14 | DB アラート欠落 | `target/alerts/alerts.yaml` × `target/runbooks/db-failover.md` | P1 runbook（db-failover）を起動するトリガとなる DB 系アラート（PostgresDown・レプリケーション遅延）が皆無（※2026-07-06 の実走 F-A9 で発見・追記） |

## 採点メモ
- D01〜D03 は静的（docs のみで検出可能）。D04/D05/D09/D10/D13 は**ライブ突合が必須**——ここが拾えていれば「ドリフト検出」が機能している。
- 監査が上記以外を指摘した場合は偽陽性か「実在するが未登録の欠陥」かを人が判定し、後者ならこの表に追記する。
