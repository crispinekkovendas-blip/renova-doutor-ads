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
VIDEOS = [
    dict(n=1, key="mora-longe", clip="clip-6-mora-longe.mp4", voice="voz3-1-mora-longe.mp3", turn=5.0,
         lines=[("Mora longe de um consultório?", "Mora longe de um consultório?"),
                ("Horas de estrada, só para uma consulta…", "Horas de estrada, só para uma consulta..."),
                ("A consulta médica pode ser por vídeo.", "Mas a consulta médica pode ser por vídeo,"),
                ("De onde você estiver.", "de onde você estiver.")]),
    dict(n=2, key="sem-tempo", clip="clip-4b-dia-corrido-e-cozinha.mp4", voice="voz3-2-sem-tempo.mp3", turn=6.1,
         lines=[("Sem tempo para ir ao consultório?", "Sem tempo para ir ao consultório?"),
                ("O dia enche… e a consulta vai ficando para depois.", "O dia enche... e a consulta vai ficando para depois."),
                ("Mas ela pode ser por vídeo, com hora marcada.", "Mas ela pode ser por vídeo, com hora marcada.")]),
    dict(n=3, key="cuida-dos-pais", clip="clip-7-cuida-dos-pais.mp4", voice="voz3-3-cuida-dos-pais.mp3", turn=5.0,
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
    dict(n=5, key="funciona", clip="clip-8-funciona.mp4", voice="voz3-5-funciona.mp3", turn=5.0,
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
    total = v.duration(clip)
    at_a = LEAD
    end_a = at_a + pa[-1][1] - pa[0][0]
    at_b = end_a + 0.35                          # a short breath, then the standard ending
    end_b = at_b + pb[-1][1] - pb[0][0]
    at_c = max(end_b + 0.35, total + 0.2)        # the emergency line waits for the closing card
    captions = [c for c, _ in vd["lines"]] + [c for c, _ in END_LINES]
    starts = (caption_times(pa, [s for _, s in vd["lines"]], at_a)
              + caption_times(pb, [s for _, s in END_LINES], at_b))
    keep = [k for k, s in enumerate(starts) if s < total - 0.6]      # later ones would fall on the closing card
    captions, starts = [captions[k] for k in keep], [starts[k] for k in keep]
    print("\n" + name, "| clip %.2f s | opening %.2f-%.2f | ending %.2f-%.2f | emergency line from %.2f"
          % (total, at_a, end_a, at_b, end_b, at_c), flush=True)
    for s, c in zip(starts, captions):
        print("   %5.2f  %s" % (s, c), flush=True)
    mp4 = v.dress_clip(name, clip, captions, starts=starts, music=True, turn=vd.get("turn"), voice=voice,
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
