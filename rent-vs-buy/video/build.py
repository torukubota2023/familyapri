"""解説動画ビルダー: scenes.json → 画像(Playwright) + 音声(Open JTalk) → MP4(ffmpeg)

使い方: python3 build.py  （出力: out/rent_vs_buy_naha.mp4）
"""
import json, subprocess, wave, pathlib, re, shutil
import numpy as np
import pyopenjtalk

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"
WORK = HERE / "work"
SPEED = 1.0
GAP = 0.45  # 文と文の間の無音（秒）


def tts(text, path):
    x, sr = pyopenjtalk.tts(text, speed=SPEED)
    pad = np.zeros(int(sr * GAP))
    x = np.concatenate([x, pad])
    x = (x / max(1.0, np.abs(x).max()) * 29000).astype(np.int16)  # ピーク約 -1dBFS に正規化（音割れ防止）
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(x.tobytes())
    return len(x) / sr


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
    # 音声＋クリップ
    lst = []
    for stem, speech in jobs:
        dur = tts(speech, WORK / f"{stem}.wav")
        clip = WORK / f"{stem}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(WORK / f"{stem}.png"),
                        "-i", str(WORK / f"{stem}.wav"), "-c:v", "libx264", "-tune", "stillimage",
                        "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
                        "-t", f"{dur:.3f}", "-shortest", str(clip)], check=True)
        lst.append(f"file '{clip.name}'")
    (WORK / "list.txt").write_text("\n".join(lst))
    final = OUT / "rent_vs_buy_naha.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(WORK / "list.txt"),
                    "-c", "copy", "-movflags", "+faststart", str(final)], check=True, cwd=WORK)
    # 字幕ファイル（SRT）も出力
    t, srt = 0.0, []
    for i, (stem, speech) in enumerate(jobs, 1):
        with wave.open(str(WORK / f"{stem}.wav")) as w:
            d = w.getnframes() / w.getframerate()
        f = lambda s: f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d},{int(s*1000%1000):03d}"
        srt.append(f"{i}\n{f(t)} --> {f(t+d)}\n{captions[stem]}\n")
        t += d
    (OUT / "rent_vs_buy_naha.srt").write_text("\n".join(srt), encoding="utf-8")
    print(f"done: {final} ({t/60:.1f} min, {len(jobs)} clips)")


if __name__ == "__main__":
    main()
