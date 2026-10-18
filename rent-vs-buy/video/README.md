# 解説動画のつくり方

`out/rent_vs_buy_naha.mp4`（1920×1080、約14分）と字幕 `out/rent_vs_buy_naha.srt` を作る。
ナレーションは VOICEVOX:玄野武宏（ノーマル、スタイルID 11）、右下に口パクする猫アバター。

## 構成

| ファイル | 役割 |
|---|---|
| `make_scenes.py` | 場面ごとの画面（HTML）とナレーション文を `scenes.json` に書き出す。数値は `../model.py` の計算結果をそのまま使う |
| `template.html` | 画面の共通デザイン（下部に字幕帯、左下に「VOICEVOX:玄野武宏」を常時表示） |
| `shoot.mjs` | Playwright（Chromium）で各画面を PNG にする |
| `build.py` | VOICEVOX で音声を作り、音量から口の形（閉・半開・開・瞬き）を決めて猫を重ね、ffmpeg で MP4 と SRT にする |
| `avatar/` | 猫アバターの透明PNG（`closed` / `half` / `open` / `blink`）。いまは `draw_placeholder.mjs` で描いた仮の猫 |

本番の猫アバターに差し替えるときは、`avatar/` の4枚を同じ名前の透明PNG（正方形）で置き換えて `build.py` を実行し直す。

## VOICEVOX CORE の準備（0.16.0）

GitHub Releases から直接取得する（API 経由のダウンローダーが使えない環境向け）。

```sh
B=https://github.com/VOICEVOX
curl -LO $B/voicevox_core/releases/download/0.16.0/voicevox_core-0.16.0-cp310-abi3-manylinux_2_34_x86_64.whl
curl -LO $B/voicevox_vvm/releases/download/0.16.0/4.vvm        # 玄野武宏を含む音声モデル
curl -LO $B/onnxruntime-builder/releases/download/voicevox_onnxruntime-1.17.3/voicevox_onnxruntime-linux-x64-1.17.3.tgz
tar xzf voicevox_onnxruntime-linux-x64-1.17.3.tgz
pip install voicevox_core-0.16.0-*.whl pyopenjtalk numpy pillow   # 辞書は pyopenjtalk が取得する open_jtalk_dic_utf_8-1.11 を使う

export VV_ORT=$PWD/voicevox_onnxruntime-linux-x64-1.17.3/lib/libvoicevox_onnxruntime.so.1.17.3
export VV_DICT=$(python3 -c "import pyopenjtalk,os;print(os.path.join(os.path.dirname(pyopenjtalk.__file__),'open_jtalk_dic_utf_8-1.11'))")
export VV_VVM=$PWD/4.vvm
```

## 再生成

```sh
python3 make_scenes.py
python3 build.py      # 作業ファイルは work/ に出力（git 管理外）
```

音声の利用条件：「VOICEVOX:玄野武宏」のクレジット表記で商用・非商用とも利用可（VOICEVOX 音声ライブラリ利用規約）。
