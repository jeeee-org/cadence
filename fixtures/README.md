# fixtures — cadence 実走検証用の合成インフラリポ

`audit-reliability` フローを **infra MCP なしで実走検証**するためのテストベッド。
小さな偽インフラリポ（runbook / IaC / アラート定義）に**既知の欠陥を意図的に仕込み**、
「監査が何件拾えるか」を採点できるようにしてある。

## 構成
```
fixtures/
├── README.md        # このファイル
├── EXPECTED.md      # ⚠️ 仕込んだ欠陥の正解リスト（採点用。監査エージェントは読まないこと）
├── target/          # 監査対象（docs / source of truth）
│   ├── runbooks/
│   ├── terraform/
│   ├── k8s/
│   └── alerts/
└── live-state/      # 擬似ライブ状態（read-only infra MCP の代わり。JSON を Read で読む）
```

## 使い方
```
/cadence audit-reliability fixtures/target
```
のように監査対象を `fixtures/target` にし、フローの `mcp: infra` の代替として
**`fixtures/live-state/*.json` を「MCP から取得したライブ状態」と見なして Read する**。

## 採点
実走後、最終レポートの findings を `EXPECTED.md` の欠陥リストと突き合わせる：
- **検出**: EXPECTED の欠陥を file:line / live-state 参照つきで指摘できたか
- **偽陽性**: EXPECTED に無い指摘は、実在の欠陥か言いがかりかを人が判定
- **read-only**: ラン中に fixtures/ 配下が一切変更されていないか（`git status` で確認）

## ⚠️ 監査エージェントへの注意
このラン（フィクスチャ実走）では **`fixtures/EXPECTED.md` と `fixtures/README.md` を読んではいけない**。
正解を見た監査は検証にならない。監査対象は `fixtures/target/` と `fixtures/live-state/` のみ。
