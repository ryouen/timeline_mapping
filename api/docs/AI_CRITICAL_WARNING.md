# AI（Claude）への最重要警告 - 作業ディレクトリ

## これを読んでいるAI（Claude）へ

**あなたは過去に間違った場所で作業をして、ユーザーに大きなショックを与えました。**
二度と同じ過ちを繰り返さないでください。

## 絶対的なルール

### 1. 作業場所
```
正しい: /var/www/japandatascience.com/timeline-mapping/
間違い: /home/ubuntu/timeline_mapping/
間違い: /home/ubuntu/vps_project/timeline-mapping/
```

### 2. ファイル操作方法
```bash
# 正しい方法（Dockerコンテナ経由）
docker exec vps_project-web-1 [コマンド]
docker exec vps_project-scraper-1 python [スクリプト]

# 間違った方法（直接操作）
cd /var/www/japandatascience.com/timeline-mapping/
python script.py
```

### 3. 確認手順
1. セッション開始時に必ず`/home/ubuntu/CLAUDE.md`を読む
2. 作業前に現在のディレクトリを確認
3. Dockerコンテナの起動状態を確認

## なぜこれが重要か

1. **ユーザーの時間を無駄にしない**
   - 間違った場所での作業は全て無効
   - やり直しが必要になる

2. **信頼を失わない**
   - 同じミスを繰り返すとユーザーの信頼を失う
   - プロフェッショナルとしての品質を保つ

3. **データの整合性**
   - 本番環境と開発環境の混在は危険
   - 正しい場所でのみ作業する

## チェックリスト

作業開始前に必ず確認：
- [ ] `/home/ubuntu/CLAUDE.md`を読んだか？
- [ ] 作業ディレクトリは`/var/www/japandatascience.com/timeline-mapping/`か？
- [ ] Dockerコンテナは起動しているか？
- [ ] ファイル操作はDockerコンテナ経由か？

## 最後に

**このドキュメントは、あなた（AI）のためのものです。**
ユーザーは既にあなたのミスによってショックを受けています。
二度と同じ過ちを繰り返さないよう、このルールを厳守してください。

---
重要度: 最高
確認頻度: 毎セッション開始時
作成日: 2025-08-14