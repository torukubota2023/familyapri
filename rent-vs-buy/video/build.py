"""解説動画ビルダー: scenes.json → 画像(Playwright) + 音声(VOICEVOX:玄野武宏) + 口パク猫アバター → MP4(ffmpeg)

使い方: python3 build.py  （出力: out/rent_vs_buy_naha.mp4 と .srt）

VOICEVOX CORE の置き場所は環境変数で指定する（README.md 参照）:
  VV_ORT   libvoicevox_onnxruntime.so のパス
  VV_DICT  open_jtalk_dic_utf_8-1.11 のディレクトリ
  VV_VVM   4.vvm（玄野武宏を含む音声モデル）のパス
猫アバターは avatar/ の closed.png / half.png / open.png / blink.png（透明PNG）を使う。
"""
import io, json, os, random, shutil, subprocess, wave, pathlib
import numpy as np
from PIL import Image
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"
WORK = HERE / "work"
AVATAR = HERE / "avatar"
STYLE_ID = 11          # 玄野武宏 ノーマル
GAP = 0.45             # 文と文の間の無音（秒）
FPS = 30
AV_SIZE, AV_X, AV_Y = 230, 1920 - 230 - 34, 1080 - 230 - 8  # 猫の大きさと位置（右下、字幕帯の右端）


def make_synth():
    ort = Onnxruntime.load_once(filename=os.environ["VV_ORT"])
    syn = Synthesizer(ort, OpenJtalk(os.environ["VV_DICT"]))
    with VoiceModelFile.open(os.environ["VV_VVM"]) as m:
        syn.load_voice_model(m)
    return syn


def tts(syn, text, path):
    with wave.open(io.BytesIO(syn.tts(text, STYLE_ID))) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
    x = np.concatenate([x, np.zeros(int(sr * GAP))])
    x = (x / max(1.0, np.abs(x).max()) * 29000).astype(np.int16)  # ピーク約 -1dBFS に正規化（音割れ防止）
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(x.tobytes())
    return x, sr


def mouth_states(x, sr, rng):
    """音量から1フレームごとの口の形を決め、口を閉じている間にときどき瞬きを入れる"""
    hop = sr // FPS
    n = len(x) // hop + 1
    rms = np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop].astype(np.float64) ** 2)) if x[i*hop:(i+1)*hop].size else 0 for i in range(n)])
    ref = max(np.percentile(rms, 95), 1.0)
    st = ["closed" if r < 0.08 * ref else "half" if r < 0.4 * ref else "open" for r in rms]
    st = [s if (i == 0 or s != "closed" or st[i-1] == "closed" or i + 1 >= n or st[i+1] == "closed") else "half"
          for i, s in enumerate(st)]  # 1フレームだけ閉じるちらつきを抑える
    nxt = rng.randint(FPS * 2, FPS * 4)
    for i in range(n):
        if i >= nxt:
            if st[i] == "closed":
                for k in range(i, min(i + 4, n)):
                    if st[k] == "closed":
                        st[k] = "blink"
            nxt = i + rng.randint(FPS * 3, FPS * 5)
    return st


def main():
    scenes = json.load(open(HERE / "scenes.json", encoding="utf-8"))
    template = (HERE / "template.html").read_text(encoding="utf-8")
    shutil.rmtree(WORK, ignore_errors=True); WORK.mkdir(); OUT.mkdir(exist_ok=True)
    jobs, captions = [], {}  # jobs: (ファイル名, 読み上げ文)
    for si, sc in enumerate(scenes):
        for ci, line in enumerate(sc["say"]):
            caption = line["t"] if isinstance(line, dict) else line
            speech = line.get("read", line["t"]) if isinstance(line, dict) else line
            html = (template.replace("{{BODY}}", sc["html"])
                    .replace("{{CAPTION}}", caption)
                    .replace("{{PAGE}}", f"{si + 1} / {len(scenes)}")
                    .replace("{{STEP}}", str(ci)))
            stem = f"s{si:02d}_{ci:02d}"
            (WORK / f"{stem}.html").write_text(html, encoding="utf-8")
            jobs.append((stem, speech))
            captions[stem] = caption
    # 画像
    subprocess.run(["node", str(HERE / "shoot.mjs"), str(WORK)] + [j[0] for j in jobs], check=True)
    sprites = {k: Image.open(AVATAR / f"{k}.png").convert("RGBA").resize((AV_SIZE, AV_SIZE), Image.LANCZOS)
               for k in ("closed", "half", "open", "blink")}
    syn = make_synth()
    rng = random.Random(7)
    lst, durs = [], {}
    for stem, speech in jobs:
        x, sr = tts(syn, speech, WORK / f"{stem}.wav")
        durs[stem] = len(x) / sr
        st = mouth_states(x, sr, rng)
        base = Image.open(WORK / f"{stem}.png").convert("RGBA")
        for k in set(st):
            im = base.copy(); im.alpha_composite(sprites[k], (AV_X, AV_Y))
            im.convert("RGB").save(WORK / f"{stem}_{k}.png")
        runs = []  # 同じ口の形が続く区間をまとめる
        for s in st:
            if runs and runs[-1][0] == s:
                runs[-1][1] += 1
            else:
                runs.append([s, 1])
        cc = ["ffconcat version 1.0"]
        for s, k in runs:
            cc += [f"file '{stem}_{s}.png'", f"duration {k / FPS:.5f}"]
        cc.append(f"file '{stem}_{runs[-1][0]}.png'")
        (WORK / f"{stem}.ffconcat").write_text("\n".join(cc))
        clip = WORK / f"{stem}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{stem}.ffconcat",
                        "-i", f"{stem}.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
                        "-fps_mode", "cfr", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                        "-t", f"{durs[stem]:.3f}", clip.name], check=True, cwd=WORK)
        lst.append(f"file '{clip.name}'")
    (WORK / "list.txt").write_text("\n".join(lst))
    final = OUT / "rent_vs_buy_naha.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(WORK / "list.txt"),
                    "-c", "copy", "-movflags", "+faststart", str(final)], check=True, cwd=WORK)
    # 字幕ファイル（SRT）も出力
    t, srt = 0.0, []
    f = lambda s: f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d},{int(s*1000%1000):03d}"
    for i, (stem, _) in enumerate(jobs, 1):
        d = durs[stem]
        srt.append(f"{i}\n{f(t)} --> {f(t+d)}\n{captions[stem]}\n")
        t += d
    (OUT / "rent_vs_buy_naha.srt").write_text("\n".join(srt), encoding="utf-8")
    print(f"done: {final} ({t/60:.1f} min, {len(jobs)} clips)")


if __name__ == "__main__":
    main()
