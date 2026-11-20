"""Video ads, vertical 1080x1920.

Two kinds:
  text   a text-led video drawn on this PC from a web page (no Higgsfield, no credits)
  clip   a Higgsfield clip dressed with the signature line and timed captions

Usage:
    python -X utf8 build_video.py text chat           the booking-chat video
    python -X utf8 build_video.py clip NAME SOURCE.mp4 "caption 1|caption 2|caption 3"
        captions share the time equally; write "0.5::caption 1|6.2::caption 2" to set each start
        a caption that starts with "!" is the call to action and is drawn as a green button
        add --music for the soundtrack made by build_music.py, and --turn 6.1 for a story ad
        (the second where the picture cuts from the problem to the solution)
        add --voice NARRATION.mp3 for a narrator who reads the captions: the file is cut at its
        pauses and each line starts with its caption; --group 3,1,1,1,1 when one caption takes
        several spoken stretches
        add --voice-at 0.6 to play the narration uncut from that second instead (a narrator who
        tells the story in flowing sentences); then give every caption its own start time
        --voice-at 0.5,6.2,10.9 --group 2,1,2 plays it in three uncut sections (of 2, 1 and 2
        spoken stretches) that start at those seconds, to line the story up with the picture's cuts
        in a caption, *words* get a yellow highlight (and the caption is drawn larger) and ^ starts
        a new line: "10.9::*Não é SUS.*^É consulta particular."
        every clip ends on a closing card (clinic, NÃO É SUS, the button, the emergency line, the
        doctor); --end 6 sets how many seconds it stays, --end 0 leaves it out
    the yellow NÃO É SUS tag, the signature and the small print with the doctor's name are on screen
    the whole time; their words come from DOCTOR in build_ads.py
    add --still 6.5 to save one frame as a PNG instead of the video (for checking; text videos only)

Texts that must stay inside the part of the screen Instagram does not cover:
top 14% and bottom 35% of a Reel are hidden by its own buttons, so everything
that must be read sits between y=290 and y=1250.
"""
import html
import pathlib
import re
import shutil
import subprocess
import sys

import build_ads as b

HERE = pathlib.Path(__file__).resolve().parent
WORK = HERE / "work"
OUT = HERE / "video"
W, H, FPS = 1080, 1920, 30
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
e = html.escape

FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&'
         'family=DM+Sans:wght@400;500;700;800&display=swap" rel="stylesheet">')

# ---------------------------------------------------------------- text-led: booking chat

CHAT_CSS = """
*{box-sizing:border-box}
html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#F4EFE6}
.stage{position:relative;width:1080px;height:1920px;overflow:hidden;background:#F4EFE6;color:#12312F;
  font-family:'DM Sans','Segoe UI',sans-serif}
.d1{position:absolute;right:-220px;top:-160px;width:620px;height:620px;border-radius:50%;background:#E3DACB;opacity:.8}
.d2{position:absolute;left:-170px;bottom:120px;width:420px;height:420px;border-radius:50%;border:34px solid #E3DACB;opacity:.7}
.d3{position:absolute;right:90px;bottom:330px;width:150px;height:150px;border-radius:50%;background:#DCE5DA;opacity:.9}
.wrap{position:absolute;left:64px;right:64px;top:300px}
.kicker{font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:27px;color:#1F6F5F}
h1{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:86px;line-height:1.04;margin:14px 0 0;letter-spacing:-.01em}
.chat{margin-top:30px;background:#fff;border-radius:34px;box-shadow:0 18px 50px rgba(18,49,47,.14);overflow:hidden}
.top{display:flex;align-items:center;gap:20px;padding:18px 26px;background:#12312F;color:#F4EFE6}
.av{width:62px;height:62px;border-radius:50%;background:#8FD3B6;color:#12312F;font-weight:700;font-size:27px;
  display:flex;align-items:center;justify-content:center;flex:none}
.top b{display:block;font-size:30px}
.top span{display:block;font-size:22px;opacity:.8;margin-top:2px}
.body{padding:20px 22px 24px;background:#EFE9DD;display:flex;flex-direction:column;gap:18px}
.row{position:relative;display:flex}
.row.me{justify-content:flex-end}
.msg{max-width:84%;padding:22px 26px;border-radius:24px;font-size:35px;line-height:1.26;box-shadow:0 2px 5px rgba(0,0,0,.08)}
.me .msg{background:#CFEFD9;border-bottom-right-radius:8px}
.you .msg{background:#fff;border-bottom-left-radius:8px}
.typing{position:absolute;left:0;top:0;background:#fff;border-radius:26px;border-bottom-left-radius:8px;
  padding:28px 28px;display:flex;gap:11px;box-shadow:0 2px 5px rgba(0,0,0,.08);opacity:0}
.typing i{display:block;width:15px;height:15px;border-radius:50%;background:#7C8B88}
.sim{margin-top:14px;font-size:21px;color:#5A6B68;text-align:center}
.sig{margin-top:18px;background:#12312F;color:#F4EFE6;border-radius:30px;
  padding:22px 28px;display:flex;align-items:center;justify-content:space-between;gap:20px}
.sig .n{font-weight:700;font-size:31px}
.sig .c{font-size:23px;margin-top:4px;opacity:.9}
.cta{background:#8FD3B6;color:#12312F;font-weight:700;font-size:26px;padding:18px 24px;border-radius:999px;white-space:nowrap}
[data-in]{opacity:0}
"""

CHAT_JS = """
function ease(p){p=Math.max(0,Math.min(1,p));return 1-Math.pow(1-p,3)}
function renderAt(t){
  document.querySelectorAll('[data-in]').forEach(function(el){
    var p=ease((t-parseFloat(el.dataset.in))/0.38);
    el.style.opacity=p;
    el.style.transform='translateY('+((1-p)*26)+'px) scale('+(0.97+0.03*p)+')';
  });
  document.querySelectorAll('.typing').forEach(function(el){
    var a=parseFloat(el.dataset.from),z=parseFloat(el.dataset.to);
    var p=Math.min(ease((t-a)/0.2),1-ease((t-z+0.12)/0.12));
    el.style.opacity=Math.max(0,p);
    el.querySelectorAll('i').forEach(function(d,k){
      var s=Math.sin(2*Math.PI*(t*1.5-k*0.17));
      d.style.transform='translateY('+(-7*Math.max(0,s))+'px)';
      d.style.opacity=0.55+0.45*Math.max(0,s);
    });
  });
  var c=document.querySelector('.cta'),t0=parseFloat(c.dataset.pulse);
  var k=t>t0?1+0.07*Math.max(0,Math.sin(2*Math.PI*(t-t0)*0.9)):1;
  c.style.transform='scale('+k+')';
}
"""


def chat_page(ad_number=77):
    a = b.ADS[ad_number - 1]
    times = []          # (when the message lands, when "typing" starts or None)
    t = 1.3
    for who, text in a["chat"]:
        if who == "you":
            times.append((t + 1.15, t))
            t += 1.15 + 1.9
        else:
            times.append((t, None))
            t += 1.1
    rows = ""
    for (who, text), (land, typing) in zip(a["chat"], times):
        dots = ('<div class="typing" data-from="%.2f" data-to="%.2f"><i></i><i></i><i></i></div>' % (typing, land)
                if typing is not None else "")
        rows += ('<div class="row ' + who + '">' + dots + '<div class="msg" data-in="%.2f">' % land
                 + e(text) + "</div></div>")
    end = times[-1][0] + 1.6
    page = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">' + FONTS + "<style>" + CHAT_CSS
            + '</style></head><body><div class="stage"><div class="d1"></div><div class="d2"></div><div class="d3"></div>'
            '<div class="wrap"><div class="kicker" data-in="0.15">' + e(a["kicker"]) + '</div><h1 data-in="0.35">'
            + e(a["h"]) + '</h1><div class="chat" data-in="0.75"><div class="top"><div class="av">'
            + e(b.DOCTOR["initials"]) + "</div><div><b>Agendamento</b><span>" + e(b.DOCTOR["name"])
            + '</span></div></div><div class="body">' + rows + "</div></div>"
            '<div class="sim" data-in="0.75">Simulação ilustrativa de uma conversa de agendamento.</div>'
            '<div class="sig"><div><div class="n">' + e(b.DOCTOR["name"]) + '</div><div class="c">'
            + e(b.DOCTOR["line1"]) + '</div></div><div class="cta" data-pulse="%.2f">' % end + e(b.CTA)
            + "</div></div></div></div><script>" + CHAT_JS + "</script></body></html>")
    return page, end + 3.2


# ---------------------------------------------------------------- drawing frames

def render_page(page_html, name, seconds, still=None):
    """Draws the page frame by frame with Chrome and hands the frames to ffmpeg."""
    from playwright.sync_api import sync_playwright
    WORK.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    src = WORK / ("video-" + name + ".html")
    src.write_text(page_html, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True, args=["--hide-scrollbars"])
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(src.as_uri())
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(400)
        if still is not None:
            page.evaluate("renderAt(%f)" % still)
            png = OUT / (name + "-frame.png")
            page.screenshot(path=str(png))
            browser.close()
            return png
        mp4 = OUT / (name + ".mp4")
        ff = subprocess.Popen(
            [FFMPEG, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
             str(mp4)], stdin=subprocess.PIPE)
        total = int(round(seconds * FPS))
        for n in range(total):
            page.evaluate("renderAt(%f)" % (n / FPS))
            ff.stdin.write(page.screenshot(type="jpeg", quality=95))
            if n % 60 == 0:
                print("frame", n, "of", total, flush=True)
        ff.stdin.close()
        ff.wait()
        browser.close()
        return mp4


# ---------------------------------------------------------------- Higgsfield clip + captions

OVER_CSS = """
*{box-sizing:border-box}
html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:transparent}
.o{position:relative;width:1080px;height:1920px;font-family:'DM Sans','Segoe UI',sans-serif;color:#fff}
.tag{position:absolute;left:0;right:0;top:%(tag_top)dpx;text-align:center}
.tag span{display:inline-flex;border-radius:16px;overflow:hidden;box-shadow:0 6px 22px rgba(0,0,0,.5);
  font-weight:800;font-size:42px;line-height:1}
.tag b{background:#FFD400;color:#111;padding:18px 24px;letter-spacing:.02em}
.tag i{font-style:normal;background:#fff;color:#111;padding:18px 24px}
.sig{position:absolute;left:0;right:0;top:%(sig_top)dpx;text-align:center}
.sig span{display:inline-block;background:rgba(10,24,23,.74);border-radius:16px;padding:10px 26px;font-size:27px;line-height:1.3}
.sig .cl{display:block;font-size:33px;font-weight:700}
.fine{position:absolute;left:0;right:0;top:%(fine_top)dpx;text-align:center;font-size:24px;
  text-shadow:0 1px 4px rgba(0,0,0,.95),0 0 14px rgba(0,0,0,.75)}
.cap{position:absolute;left:70px;right:70px;bottom:%(cap_bottom)dpx;text-align:center;text-wrap:balance}
.cap span{display:inline;background:#fff;color:#111;font-weight:700;font-size:50px;line-height:1.5;padding:8px 20px;
  border-radius:14px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.cap.big span{font-size:64px}
.cap mark{background:#FFD400;color:#111;padding:2px 12px;border-radius:10px}
.btn span{display:inline-block;background:#1FA855;color:#fff;font-size:54px;line-height:1.2;padding:20px 44px;
  border-radius:999px;box-shadow:0 8px 26px rgba(0,0,0,.35)}
.btn small{display:block;font-size:29px;font-weight:500;margin-top:4px}
"""

END_CSS = """
*{box-sizing:border-box}
html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#F4EFE6}
.o{position:relative;width:1080px;height:1920px;font-family:'DM Sans','Segoe UI',sans-serif;background:#F4EFE6;color:#12312F}
.wrap{position:absolute;left:60px;right:60px;top:318px;text-align:center}
h1{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:88px;line-height:1.1;margin:0}
.no{display:inline-block;margin-top:30px;background:#FFD400;color:#111;font-weight:800;font-size:104px;line-height:1.1;
  padding:16px 44px;border-radius:22px}
.gov{margin-top:14px;font-size:38px;font-weight:700}
.what{margin-top:30px;font-size:50px;font-weight:700;line-height:1.24}
.btn{display:inline-block;margin-top:40px;background:#1FA855;color:#fff;font-size:52px;font-weight:700;line-height:1.15;
  padding:22px 48px;border-radius:999px;box-shadow:0 8px 26px rgba(0,0,0,.22)}
.btn small{display:block;font-size:29px;font-weight:500;margin-top:4px}
.emer{margin-top:40px;font-size:33px;line-height:1.35;font-weight:500}
.fine2{margin-top:24px;font-size:24px;color:#4a5b58}
"""
XFADE = 0.35      # seconds the clip takes to dissolve into the end card


def rich(text):
    """Caption text as HTML: *words* get the yellow highlight, ^ starts a new line."""
    return re.sub(r"\*(.+?)\*", r"<mark>\1</mark>", e(text)).replace("^", "<br>")


def overlay_png(name, caption, ill_top, sig_top):
    """A see-through picture: either the signature (always on screen) or one caption.

    The signature sits low, under the captions and away from any face, so nobody reads the
    doctor's name as a label for the person in the picture."""
    from playwright.sync_api import sync_playwright
    css = OVER_CSS % {"tag_top": ill_top + 8, "sig_top": sig_top, "fine_top": sig_top + 108,
                      "cap_bottom": H - sig_top + 18}
    d = b.DOCTOR
    if caption.startswith("!"):      # "!text" is the call to action, drawn as a green button
        text, _, small = caption[1:].partition("//")   # "!button // small" adds a small second line inside it
        body = ('<div class="cap btn"><span>' + e(text.strip())
                + ("<small>" + e(small.strip()) + "</small>" if small.strip() else "") + "</span></div>")
    elif caption:                    # a caption with a *highlight* is drawn larger
        body = '<div class="cap%s"><span>%s</span></div>' % (" big" if "*" in caption else "", rich(caption))
    else:                            # what stays on screen the whole time
        clinic = d.get("clinic", "").strip()
        tag = ""
        if d.get("tag_no"):          # the yellow NÃO É SUS tag, at the top of the readable area
            tag = ('<div class="tag"><span><b>' + e(d["tag_no"]) + "</b>"
                   + ("<i>" + e(d["tag_what"]) + "</i>" if d.get("tag_what") else "") + "</span></div>")
        body = (tag + '<div class="sig"><span>' + ('<b class="cl">' + e(clinic) + "</b>" if clinic else "")
                + e(d.get("service", "")) + "</span></div>"
                + '<div class="fine">Médico: ' + e(d["name"]) + " · " + e(d["crm"]) + " · Imagem ilustrativa</div>")
    doc = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">' + FONTS + "<style>" + css
           + '</style></head><body><div class="o">' + body + "</div></body></html>")
    src = WORK / ("video-" + name + ".html")
    src.write_text(doc, encoding="utf-8")
    png = WORK / ("video-" + name + ".png")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(src.as_uri())
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(300)
        page.screenshot(path=str(png), omit_background=True)
        browser.close()
    return png


def end_card_png(name):
    """The card that closes a video: clinic, a large NÃO É SUS, what the service is, the button,
    the emergency line and the doctor. All the words come from DOCTOR in build_ads.py."""
    from playwright.sync_api import sync_playwright
    d = b.DOCTOR

    def lines(key):
        return e(d.get(key, "")).replace("|", "<br>")

    body = ('<div class="wrap"><h1>' + e(d.get("clinic") or d["name"]) + "</h1>"
            + ('<div class="no">' + e(d["tag_no"]) + "</div>" if d.get("tag_no") else "")
            + ('<div class="gov">' + lines("gov") + "</div>" if d.get("gov") else "")
            + ('<div class="what">' + lines("offer") + "</div>" if d.get("offer") else "")
            + '<div class="btn">' + e(d.get("cta") or b.CTA)
            + ("<small>" + e(d["cta_small"]) + "</small>" if d.get("cta_small") else "") + "</div>"
            + ('<div class="emer">' + lines("emergency") + "</div>" if d.get("emergency") else "")
            + '<div class="fine2">Médico: ' + e(d["name"]) + " · " + e(d["crm"]) + "</div></div>")
    doc = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">' + FONTS + "<style>" + END_CSS
           + '</style></head><body><div class="o">' + body + "</div></body></html>")
    src = WORK / ("video-" + name + ".html")
    src.write_text(doc, encoding="utf-8")
    png = WORK / ("video-" + name + ".png")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(src.as_uri())
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(300)
        page.screenshot(path=str(png))
        browser.close()
    return png


def duration(path):
    r = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def loudness(path):
    """How loud a sound file is overall, in LUFS (the unit streaming platforms use)."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    found = [ln.split()[1] for ln in r.stderr.splitlines() if ln.strip().startswith("I:")]
    return float(found[-1]) if found else -20.0


def speech_parts(path, noise=-38, gap=0.16):
    """Start and end of each spoken stretch in a narration file; the pauses between sentences split it."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-af",
                        "silencedetect=noise=%ddB:d=%.2f" % (noise, gap), "-f", "null", "-"],
                       capture_output=True, text=True)
    total = duration(path)
    quiet, start = [], None
    for ln in r.stderr.splitlines():
        if "silence_start:" in ln:
            start = max(0.0, float(ln.split("silence_start:")[1].split()[0]))
        elif "silence_end:" in ln and start is not None:
            quiet.append((start, float(ln.split("silence_end:")[1].split()[0])))
            start = None
    if start is not None:
        quiet.append((start, total))
    parts, at = [], 0.0
    for a, z in quiet:
        if a - at > 0.05:
            parts.append((at, a))
        at = z
    if total - at > 0.05:
        parts.append((at, total))
    return parts


def dress_clip(name, source, captions, ill_top=292, sig_top=None, lead=0.4, starts=None, music=False, turn=None,
               voice=None, groups=None, voice_at=None, end_card=5.0):
    """Clip on a blurred copy of itself (fills 9:16), signature all the time, captions one after another.

    music=True adds the soundtrack from build_music.py; turn is the second where a story cuts
    from the problem to the solution, so the music opens up at that moment.
    voice is a narration file that reads the captions in order. It is cut at its pauses and each
    line starts together with its caption; groups says how many spoken stretches belong to each
    caption (default one each). With a voice the music plays much quieter underneath.
    voice_at (seconds) plays the narration uncut from that second instead: use it for a narrator who
    tells the story in flowing sentences, and give each caption the second its phrase is spoken."""
    OUT.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=True)
    total = duration(source)
    if sig_top is None:      # two signature lines and the small print under them end by y=1250
        sig_top = 1106
    sig = overlay_png(name + "-sig", "", ill_top, sig_top)
    caps = [overlay_png(name + "-cap%d" % (k + 1), c, ill_top, sig_top) for k, c in enumerate(captions)]
    slot = (total - lead) / max(1, len(caps))
    starts = list(starts or [lead + k * slot for k in range(len(caps))])

    lines, hold, slow = [], 0.0, 1.0  # lines: (cut from, cut to, plays at) for each piece of the narration
    if voice:
        parts = speech_parts(voice)
        free, k, end = 0.0, 0, 0.0
        if voice_at is not None:                     # the narration plays as recorded, in uncut sections
            ats = list(voice_at)
            secs = groups if groups and len(groups) == len(ats) and sum(groups) == len(parts) else None
            if secs is None:                         # no valid split given: one section, the whole narration
                if len(ats) > 1:
                    print("narration has %d spoken parts, sections expect %s: playing it whole" % (len(parts), groups))
                secs, ats = [len(parts)], ats[:1]
            said = []
            for n, at in zip(secs, ats):
                a, z = parts[k][0], parts[k + n - 1][1]
                at = max(at, free)                   # a section never starts before the one before it ended
                lines.append((max(0.0, a - 0.05), z + 0.08, at))
                said += ["%.2f" % (at + 0.05 + p[0] - a) for p in parts[k:k + n]]
                end = at + (z - a)
                free = end + 0.15
                k += n
            print("spoken parts start at:", ", ".join(said))
            groups = []
        else:
            groups = groups or [1] * len(caps)
            if not (len(groups) == len(caps) and sum(groups) == len(parts)):
                print("narration has %d spoken parts, captions expect %s: playing it as one piece from the first caption"
                      % (len(parts), groups))
                groups = [len(parts)]
        for c, g in enumerate(groups):
            at = max(starts[c] + 0.1, free)          # a line never starts before the one before it ended
            if len(groups) == len(caps):
                starts[c] = at - 0.1                 # the caption appears with its line
            for j in range(g):
                a, z = parts[k]
                if j:                                # inside one caption, long dramatic pauses are shortened
                    at = end + min(a - parts[k - 1][1], 0.35)
                lines.append((max(0.0, a - 0.05), z + 0.08, at))
                end = at + (z - a)
                k += 1
            free = end + 0.25
        if end_card:                                 # the narration may run on over the end card
            end_card = max(end_card, end + 0.7 - total + XFADE)
        elif end + 0.5 > total:                      # the narration is longer than the clip
            longer = end + 0.6
            if longer / total <= 1.2:                # play the clip a little slower (hard to notice)...
                slow = longer / total
            else:                                    # ...or, if that is not enough, hold the last picture
                hold = longer - total
            total = longer
            if turn:
                turn *= slow
        print("narration:", ", ".join("%.2f-%.2f s" % (at, at + z - a) for a, z, at in lines), "| video %.2f s" % total,
              "(clip slowed to %d%%)" % round(100 / slow) if slow != 1 else "",
              "(last picture held %.2f s)" % hold if hold else "")

    cmd = [FFMPEG, "-y", "-loglevel", "error", "-i", str(source), "-loop", "1", "-t", "%.3f" % total, "-i", str(sig)]
    for c in caps:
        cmd += ["-loop", "1", "-t", "%.3f" % total, "-i", str(c)]
    f = ("[0:v]setpts=%.5f*PTS,fps=%d,tpad=stop_mode=clone:stop_duration=%.3f,split[a][c];"
         "[a]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,boxblur=28:4,"
         "eq=brightness=-0.10[bg];[c]scale=%d:-2[fg];[bg][fg]overlay=0:(H-h)/2[v0];[v0][1:v]overlay=0:0[v1]"
         % (slow, FPS, hold + 0.3, W, H, W, H, W))
    last = "v1"
    for k in range(len(caps)):
        a = starts[k]
        z = total if k == len(caps) - 1 else starts[k + 1] - 0.15
        f += (";[%d:v]format=rgba,fade=in:st=%.2f:d=0.22:alpha=1,fade=out:st=%.2f:d=0.2:alpha=1[c%d];"
              "[%s][c%d]overlay=0:0:enable='between(t,%.2f,%.2f)'[v%d]"
              % (k + 2, a, z - 0.2 if k < len(caps) - 1 else total + 1, k, last, k, a, z, k + 2))
        last = "v%d" % (k + 2)
    mp4 = OUT / (name + ".mp4")
    sound, mixed, nxt = ["-an"], [], len(caps) + 2
    length = total                                   # of the finished video
    if end_card:                                     # the clip dissolves into the closing card
        cmd += ["-loop", "1", "-t", "%.3f" % (end_card + 0.5), "-i", str(end_card_png(name + "-end"))]
        f += (";[%s]fps=%d,format=yuv420p,setsar=1,settb=AVTB,trim=duration=%.3f[m];"
              "[%d:v]fps=%d,format=yuv420p,setsar=1,settb=AVTB[ec];"
              "[m][ec]xfade=transition=fade:duration=%.2f:offset=%.3f[vend]"
              % (last, FPS, total, nxt, FPS, XFADE, total - XFADE))
        last, nxt, length = "vend", nxt + 1, total + end_card - XFADE
        print("clip %.2f s + end card %.2f s = video %.2f s" % (total, end_card, length))
    stereo = "aresample=44100,aformat=channel_layouts=stereo"
    if music:
        import build_music
        wav = build_music.write(WORK / ("video-" + name + "-music.wav"), length, turn)
        cmd += ["-i", str(wav)]
        # one fixed volume change, measured first, so the level never pumps: -16 LUFS alone, -24 under a voice
        gain = max(-30.0, min(6.0, (-24.0 if voice else -16.0) - loudness(wav)))
        f += ";[%d:a]%s,volume=%.1fdB[mus]" % (nxt, stereo, gain)
        mixed.append("[mus]")
        nxt += 1
    if voice:
        cmd += ["-i", str(voice)]
        gain = max(-12.0, min(20.0, -16.0 - loudness(voice)))
        f += ";[%d:a]%s,asplit=%d%s" % (nxt, stereo, len(lines), "".join("[q%d]" % k for k in range(len(lines))))
        for k, (a, z, at) in enumerate(lines):
            f += (";[q%d]atrim=start=%.3f:end=%.3f,asetpts=PTS-STARTPTS,afade=t=in:d=0.02,"
                  "afade=t=out:st=%.3f:d=0.05,adelay=%d:all=1[s%d]" % (k, a, z, z - a - 0.05, round(at * 1000), k))
        f += (";" + "".join("[s%d]" % k for k in range(len(lines)))
              + "amix=inputs=%d:normalize=0:duration=longest,volume=%.1fdB,apad[voc]" % (len(lines), gain))
        mixed.append("[voc]")
    if mixed:
        f += (";" + "".join(mixed) + ("amix=inputs=2:normalize=0:duration=first," if len(mixed) == 2 else "")
              + "alimiter=limit=0.89:level=disabled[aout]")
        sound = ["-map", "[aout]", "-c:a", "aac", "-b:a", "160k", "-ar", "44100"]
    cmd += ["-filter_complex", f, "-map", "[%s]" % last] + sound + ["-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-t", "%.3f" % length, str(mp4)]
    subprocess.run(cmd, check=True)
    return mp4


def main():
    args = sys.argv[1:]
    still = None
    if "--still" in args:
        k = args.index("--still")
        still = float(args[k + 1])
        del args[k:k + 2]
    turn = None
    if "--turn" in args:
        k = args.index("--turn")
        turn = float(args[k + 1])
        del args[k:k + 2]
    voice = groups = None
    if "--voice" in args:
        k = args.index("--voice")
        voice = pathlib.Path(args[k + 1])
        del args[k:k + 2]
    if "--group" in args:
        k = args.index("--group")
        groups = [int(n) for n in args[k + 1].split(",")]
        del args[k:k + 2]
    voice_at = None
    if "--voice-at" in args:
        k = args.index("--voice-at")
        voice_at = [float(n) for n in args[k + 1].split(",")]
        del args[k:k + 2]
    end_card = 5.0
    if "--end" in args:
        k = args.index("--end")
        end_card = float(args[k + 1])
        del args[k:k + 2]
    music = "--music" in args
    args = [a for a in args if a != "--music"]
    if args[:2] == ["text", "chat"]:
        page, seconds = chat_page()
        print(render_page(page, "teste-2-texto-agendamento", seconds, still), "%.1f s" % seconds)
    elif args and args[0] == "clip":
        parts = [c.strip() for c in args[3].split("|") if c.strip()]
        timed = all("::" in c for c in parts)      # "6.2::text" starts that caption at 6.2 s
        starts = [float(c.split("::")[0]) for c in parts] if timed else None
        print(dress_clip(args[1], pathlib.Path(args[2]), [c.split("::")[-1].strip() for c in parts], starts=starts,
                         music=music, turn=turn, voice=voice, groups=groups, voice_at=voice_at, end_card=end_card))
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
