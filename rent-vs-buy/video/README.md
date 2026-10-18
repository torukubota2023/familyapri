# 解説動画のつくり方

`out/rent_vs_buy_naha.mp4`（1920×1080、約16分、ナレーション付き）と、字幕ファイル `out/rent_vs_buy_naha.srt` を作ります。

## 構成

| ファイル | 役割 |
|---|---|
| `make_scenes.py` | 場面ごとの画面（HTML）とナレーション文を作り、`scenes.json` に書き出します。数値は `../model.py` で計算した結果をそのまま使います |
| `template.html` | 画面の共通デザインです（下部の帯に字幕を表示） |
| `shoot.mjs` | Playwright（Chromium）で各画面を PNG 画像にします |
| `build.py` | 次の順に処理します：<br>1. Open JTalk（pyopenjtalk）で音声を作る<br>2. ffmpeg で画像と音声を合わせて MP4 にする<br>3. SRT 字幕を作る |

## 再生成

```sh
pip install pyopenjtalk numpy   # 初回は辞書をダウンロードします
python3 make_scenes.py
python3 build.py                # 作業ファイルは work/ に出力（git 管理外）
```

前提条件（金利・売却額など）を変えるときは、`../model.py` と `make_scenes.py` を編集してから再生成してください。
