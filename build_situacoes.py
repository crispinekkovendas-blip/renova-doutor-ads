"""Video ads for the "one situation per ad" set (2026-11-19): five videos, one per situation.

Each video is a Higgsfield clip plus the narrator in three recordings:
  the opening   the situation and the offer, one recording per video (video-src\\voz3-N-*.mp3)
  the ending    "Atenção: não é SUS. É consulta particular, por chat ou por vídeo: você escolhe.
                Agende pelo WhatsApp." recorded once and used in every video (voz3-final.mp3)
  the emergency line, recorded once, played a little faster over the closing card (voz3-emergencia.mp3)
The captions are timed here from the narration itself (the pauses between sentences), so nothing
is measured by hand. The tag, the signature, the small print and the closing card come from
build_video.py, and their words from DOCTOR in build_ads.py.

This runs on GitHub (workflow build-videos.yml in the repository renova-doutor-ads), not on the
owner's PC: copy this file and any new clip or narration there, then run the workflow.

Usage:
    python -X utf8 build_situacoes.py          all five (a video whose clip is not there yet is skipped)
    python -X utf8 build_situacoes.py 2 4      only those situations

Output: video\\situacao-N-<name>.mp4, and sheets\\situacao-N-<name>.png with frames of the finished
video side by side (one every 1.5 s) so it can be checked without playing it.
"""
import pathlib
import re
import subprocess
import sys

import build_video as v

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "video-src"
WORK = HERE / "work"
SHEETS = HERE / "sheets"

LEAD = 0.5      # the second the narrator starts
GAP = 0.6       # silence put between the three recordings when they are joined into one file
FAST = 1.15     # the emergency line is played this much faster (the owner asked for it "really fast")
SNAP = 0.5      # a caption moves to a pause in the narration when one is this close (seconds)

ENDING = SRC / "voz3-final.mp3"
EMERGENCY = SRC / "voz3-emergencia.mp3"

# Each line is (caption on screen, the words the narrator says while it is on screen).
END_LINES = [
    ("*Não é SUS.*^É consulta particular.", "Atenção: não é SUS. É consulta particular,"),
    ("Por chat ou por vídeo.^*Você escolhe.*", "por chat ou por vídeo: você escolhe."),
    ("!Agende pelo WhatsApp", "Agende pelo WhatsApp."),
]

# turn: the second the picture cuts from the situation to the consultation (the music opens up there).
#       For a clip with "up" it is found by itself (the first cut), and this number is only the fallback.
# up:   the three clips made on 2026-11-19 have their faces in the middle of the frame, where the
#       captions go. up moves the picture that many pixels higher (of 1920), so mouths and chins stay
#       above the captions (the big ones start at y=888) and eyes stay under the tag (it ends at y=378).
#       One number for the whole clip, or one per shot.
# hide: per shot, blurs that many pixels at the bottom of the frame (clip 8: lettering on the mug).
VIDEOS = [
    dict(n=1, key="mora-longe", clip="clip-6-mora-longe.mp4", voice="voz3-1-mora-longe.mp3", turn=4.8, up=170,
         lines=[("Mora longe de um consultório?", "Mora longe de um consultório?"),
                ("Horas de estrada, só para uma consulta…", "Horas de estrada, só para uma consulta..."),
                ("A consulta médica pode ser por vídeo.", "Mas a consulta médica pode ser por vídeo,"),
                ("De onde você estiver.", "de onde você estiver.")]),
    dict(n=2, key="sem-tempo", clip="clip-4b-dia-corrido-e-cozinha.mp4", voice="voz3-2-sem-tempo.mp3", turn=6.1,
         lines=[("Sem tempo para ir ao consultório?", "Sem tempo para ir ao consultório?"),
                ("O dia enche… e a consulta vai ficando para depois.", "O dia enche... e a consulta vai ficando para depois."),
                ("Mas ela pode ser por vídeo, com hora marcada.", "Mas ela pode ser por vídeo, com hora marcada.")]),
    dict(n=3, key="cuida-dos-pais", clip="clip-7-cuida-dos-pais.mp4", voice="voz3-3-cuida-dos-pais.mp3", turn=4.5, up=340,
         lines=[("Cuida do seu pai ou da sua mãe?", "Cuida do seu pai ou da sua mãe?"),
                ("Levar ao consultório nem sempre é fácil.", "Levar ao consultório nem sempre é fácil."),
                ("A consulta pode ser em casa, por vídeo, com você ao lado.",
                 "A consulta pode ser em casa, por vídeo, com você ao lado.")]),
    dict(n=4, key="receita-venceu", clip="clip-5b-receita.mp4", voice="voz3-4-receita-venceu.mp3", turn=7.2,
         lines=[("A receita venceu. De novo.", "A receita venceu... de novo."),
                ("E para renovar? Trânsito, fila, sala de espera.", "E para renovar? Trânsito, fila, sala de espera."),
                ("Na Renova Doutor, a consulta é por vídeo.", "Na Renova Doutor, a consulta é por vídeo:"),
                ("O médico avalia e, quando indicado, emite a receita digital.",
                 "o médico avalia e, quando indicado, emite a receita digital.")]),
    dict(n=5, key="funciona", clip="clip-8-funciona.mp4", voice="voz3-5-funciona.mp3", turn=4.9,
         up=[110, 110, 320], hide=[0, 260, 0],     # the last shot is a close-up; the mug is in the middle shot
         lines=[("Consulta por vídeo funciona?", "Consulta por vídeo funciona?"),
                ("Funciona assim: você agenda…", "Funciona assim: você agenda,"),
                ("…e no horário marcado conversa com o médico.", "e no horário marcado conversa com o médico."),
                ("Ele ouve, avalia e orienta.", "Ele ouve, avalia e orienta.")]),
]


def run(cmd):
    """Runs a tool and, if it fails, shows what it said (on GitHub the log is all there is)."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print("failed:", " ".join(str(c) for c in cmd[:3]), "...", flush=True)
        print((r.stderr or "")[-3000:], flush=True)
        raise SystemExit(1)
    return r


def join_narration(name, opening):
    """Opening + ending + emergency line as one sound file, with a silence between them."""
    WORK.mkdir(exist_ok=True)
    out = WORK / ("voz-" + name + ".wav")
    same = "aresample=44100,aformat=sample_fmts=s16:channel_layouts=mono"
    f = ("[0:a]%s,apad=pad_dur=%.2f[a];[1:a]%s,apad=pad_dur=%.2f[b];[2:a]%s,atempo=%.2f[c];"
         "[a][b][c]concat=n=3:v=0:a=1[out]" % (same, GAP, same, GAP, same, FAST))
    run([v.FFMPEG, "-y", "-loglevel", "error", "-i", str(opening), "-i", str(ENDING), "-i", str(EMERGENCY),
         "-filter_complex", f, "-map", "[out]", str(out)])
    return out


def shot_cuts(clip, want=None):
    """The seconds where the picture cuts to another shot, found by ffmpeg's scene detection.

    want is how many cuts the clip should have: the detection then starts strict and is made more
    sensitive step by step until it finds that many (a cut between two similar pictures is weak)."""
    cuts = []
    for level in ((0.30,) if want is None else (0.40, 0.30, 0.22, 0.15, 0.10)):
        r = subprocess.run([v.FFMPEG, "-hide_banner", "-i", str(clip), "-an",
                            "-vf", "select='gt(scene,%.2f)',showinfo" % level, "-f", "null", "-"],
                           capture_output=True, text=True)
        cuts = []
        for t in (float(x) for x in re.findall(r"pts_time:\s*([0-9.]+)", r.stderr or "")):
            if t > 1.0 and (not cuts or t - cuts[-1] > 1.0):
                cuts.append(t)
        if want is None or len(cuts) >= want:
            break
    return cuts


def raise_picture(name, clip, ups, hides=None):
    """The clip with its picture moved up, so that faces stay clear of the captions and the tag.

    ups is how far, in pixels of the 1080x1920 frame: one number for the whole clip or one per
    shot. The strip left empty at the bottom shows a blurred copy of the picture. hides (one per
    shot) blurs that many pixels at the bottom of the frame during that shot. It is done at the
    clip's own frames, so the position changes exactly on the cut.
    Returns the new clip and the seconds where the shots cut."""
    ups = list(ups) if isinstance(ups, (list, tuple)) else [ups]
    hides = list(hides or [])
    shots = max(len(ups), len(hides))
    cuts = shot_cuts(clip, shots - 1 if shots > 1 else None)
    if shots > 1 and len(cuts) != shots - 1:
        print("   %s: expected %d shots but found cuts at %s: one position for the whole clip, nothing hidden"
              % (clip.name, shots, ["%.2f" % c for c in cuts]), flush=True)
        ups, hides, shots = [min(ups)], [], 1
    ups += ups[-1:] * (shots - len(ups))
    hides += [0] * (shots - len(hides))
    edge = [0.0] + [c - 0.004 for c in cuts[:shots - 1]] + [1e6]      # each shot is edge[k] to edge[k + 1]
    y = "%d" % ups[-1]
    for k in range(shots - 2, -1, -1):
        y = "if(lt(t,%.3f),%d,%s)" % (edge[k + 1], ups[k], y)
    strips = [(k, h) for k, h in enumerate(hides) if h > ups[k]]
    f = ("[0:v]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,setsar=1,split[p][q];"
         "[q]boxblur=28:4,eq=brightness=-0.10" % (v.W, v.H, v.W, v.H))
    if strips:
        f += ",split=%d[bg]%s;" % (len(strips) + 1, "".join("[b%d]" % k for k, _ in strips))
    else:
        f += "[bg];"
    f += "[bg][p]overlay=x=0:y='-(%s)':eval=frame[v0]" % y
    last = "v0"
    for n, (k, h) in enumerate(strips):
        f += (";[b%d]crop=%d:%d:0:%d[h%d];[%s][h%d]overlay=x=0:y=%d:enable='between(t,%.3f,%.3f)'[v%d]"
              % (k, v.W, h, v.H - h, k, last, k, v.H - h, edge[k], edge[k + 1] - 0.001, n + 1))
        last = "v%d" % (n + 1)
    WORK.mkdir(exist_ok=True)
    out = WORK / (name + "-raised.mp4")
    run([v.FFMPEG, "-y", "-loglevel", "error", "-i", str(clip), "-filter_complex", f, "-map", "[%s]" % last, "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(out)])
    print("   picture moved up by %s px, bottom hidden %s px | shots cut at %s"
          % (ups, hides, ", ".join("%.2f" % c for c in cuts) or "(no cut found)"), flush=True)
    return out, cuts


def caption_times(parts, said, at):
    """The second each caption appears, for one recording that starts playing at `at`.

    parts are the spoken stretches of that recording (seconds in the sound file) and said is what
    the narrator says during each caption. A caption's place is estimated from how much text comes
    before it, then moved to the start of a spoken stretch when one is close, because a new
    sentence starts after a pause."""
    first = parts[0][0]
    voiced = sum(z - a for a, z in parts)
    total = float(sum(len(s) for s in said)) or 1.0
    out, used, before = [], set(), 0
    for k, words in enumerate(said):
        want = voiced * before / total          # seconds of speech that come before this caption
        t = parts[-1][1]
        for a, z in parts:                      # the second of the file where that much has been said
            if want <= z - a:
                t = a + want
                break
            want -= z - a
        near = min(range(len(parts)), key=lambda i: abs(parts[i][0] - t))
        if k == 0:
            near = 0
        if k == 0 or (abs(parts[near][0] - t) <= SNAP and near not in used):
            t = parts[near][0]
            used.add(near)
        out.append(at + 0.05 + (t - first) - 0.12)   # a touch before the words
        before += len(words)
    for k in range(1, len(out)):                # never two captions on top of each other
        out[k] = max(out[k], out[k - 1] + 0.5)
    return out


def sheet(mp4):
    """Frames of the finished video side by side, one every 1.5 s."""
    SHEETS.mkdir(exist_ok=True)
    png = SHEETS / (mp4.stem + ".png")
    frames = int(v.duration(mp4) / 1.5) + 1
    cols = 6
    rows = (frames + cols - 1) // cols
    run([v.FFMPEG, "-y", "-loglevel", "error", "-i", str(mp4), "-vf",
         "fps=2/3,scale=288:-2,tile=%dx%d" % (cols, rows), "-frames:v", "1", str(png)])
    return png


def build(vd):
    name = "situacao-%d-%s" % (vd["n"], vd["key"])
    clip = SRC / vd["clip"]
    if not clip.exists():
        print("skip (the clip is not there yet):", name, "needs", vd["clip"], flush=True)
        return None
    opening = SRC / vd["voice"]
    voice = join_narration(name, opening)
    parts = v.speech_parts(voice)
    b1 = v.duration(opening) + GAP / 2                               # where the ending starts in the joined file
    b2 = v.duration(opening) + GAP + v.duration(ENDING) + GAP / 2    # where the emergency line starts
    pa = [p for p in parts if p[0] < b1]
    pb = [p for p in parts if b1 <= p[0] < b2]
    pc = [p for p in parts if p[0] >= b2]
    if not (pa and pb and pc):
        print("could not find the three recordings in the joined narration of", name, parts, flush=True)
        raise SystemExit(1)
    print("\n" + name, flush=True)
    turn = vd.get("turn")
    if vd.get("up") or vd.get("hide"):
        clip, cuts = raise_picture(name, clip, vd.get("up") or 0, vd.get("hide"))
        if cuts and (turn is None or abs(cuts[0] - turn) < 1.5):     # the first cut, if it is where it was seen
            turn = cuts[0]
    total = v.duration(clip)
    at_a = LEAD
    end_a = at_a + pa[-1][1] - pa[0][0]
    at_b = end_a + 0.35                          # a short breath, then the standard ending
    end_b = at_b + pb[-1][1] - pb[0][0]
    at_c = max(end_b + 0.35, total + 0.2)        # the emergency line waits for the closing card
    captions = [c for c, _ in vd["lines"]] + [c for c, _ in END_LINES]
    starts = (caption_times(pa, [s for _, s in vd["lines"]], at_a)
              + caption_times(pb, [s for _, s in END_LINES], at_b))
    # a caption with less than 1.2 s left before the closing card would only flash by: it is left out
    keep = [k for k, s in enumerate(starts) if s < total - 1.2]
    captions, starts = [captions[k] for k in keep], [starts[k] for k in keep]
    print("   clip %.2f s | opening %.2f-%.2f | ending %.2f-%.2f | emergency line from %.2f | music turns at %s"
          % (total, at_a, end_a, at_b, end_b, at_c, "%.2f" % turn if turn else "-"), flush=True)
    for s, c in zip(starts, captions):
        print("   %5.2f  %s" % (s, c), flush=True)
    mp4 = v.dress_clip(name, clip, captions, starts=starts, music=True, turn=turn, voice=voice,
                       groups=[len(pa), len(pb), len(pc)], voice_at=[at_a, at_b, at_c], end_card=5.0)
    print("built", mp4.name, "%.1f s" % v.duration(mp4), "| frames:", sheet(mp4).name, flush=True)
    return mp4


def main():
    only = set(sys.argv[1:])
    done = 0
    for vd in VIDEOS:
        if only and str(vd["n"]) not in only:
            continue
        if build(vd):
            done += 1
    print(done, "video(s) built")
    return 0


if __name__ == "__main__":
    sys.exit(main())
