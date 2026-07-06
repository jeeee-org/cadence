# cadence 改善案メモ

cadence スキルを使いながら気づいた改善ネタを溜める場所。SKILL.md の「改善案の記録（運用ルール）」に従って追記する。

このファイルが**正本**。install.sh が `~/.claude/skills/cadence/IMPROVEMENTS.md` をここへの symlink にするので、実行時の追記はそのまま git 管理下のこのファイルへ書き込まれ、再インストール（install.sh の `rm -rf`）でも消えない。

- 1件 = 日付＋状況＋気づき＋（できれば）改善案の方向性。
- 単発のタスク状況や特定 PJ のドメイン知見はここに書かない（前者は PROGRESS.md/checkpoint、後者は PJ の NOTES.md へ）。
- 同種の気づきは新規行を量産せず既存項目に統合する。

---

<!-- ここから下に追記。新しいものを上に積む。 -->

## 2026-07-06 — review↔supervise ループと ABORT 経路が自然には検証できない
- **状況**: `fixtures/` での audit-reliability 実走検証。cycle 1 で全領域被覆・issue-ready となり COMPLETE。
- **気づき**: 良い監査ほど1サイクルで収束するため、収束監視（review ループ・max_cycles 打ち切り・ABORT の部分結果報告）が実走で発火しない。この経路が一番バグりやすいのに未検証のまま残る。
- **改善案**: adversarial フィクスチャ（例：audit step に「意図的に領域を1つスキップせよ」と指示する検証専用フロー variant）を足し、supervise が gap を検出して review に戻すこと・max_cycles 到達で ABORT することを強制的に発火させる。

## 2026-07-06 — フィクスチャ検証はエンジンの正解知識に汚染される
- **状況**: 同上。エンジン（メインセッション）がフィクスチャの正解 EXPECTED.md を書いた本人だった。
- **気づき**: audit はサブエージェント（正解未読）なので公平だが、plan/supervise/fuse の品質はエンジンの事前知識と切り分けられない。
- **改善案**: 検証ランはフィクスチャを作ったセッションと**別セッション**で回すのが正。fixtures/README にその旨を明記済みだが、検証手順としても HANDOFF に固定するとよい。
