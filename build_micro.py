"""Builds the "one situation per ad" set (2026-11-19): five situations, two photos each.

Each ad speaks to one situation a person is in (never to an illness): the first line of the
caption and the label on the picture say it, and every picture carries the NÃO É SUS |
CONSULTA PARTICULAR tag, the clinic, the doctor's name, MÉDICO and the CRM.

Usage:
    python -X utf8 build_micro.py            build all ten pictures, the sheet, the list and the page
    python -X utf8 build_micro.py 1A 4B      build only those pictures (list and page are rewritten too)

Photos are reused from photos-native (no new credits). The doctor's data and the tag wording
come from build_ads.py, so a change there applies here too. Output: out-micro\\, plus
anuncios-micro.csv, micro.html and sheets\\micro.png.
"""
import csv
import html
import os
import pathlib
import subprocess
import sys

import build_ads as b

# On GitHub (Linux) the workflow points CHROME at the runner's Chrome; on Windows build_ads' path is used.
b.CHROME = os.environ.get("CHROME") or b.CHROME

HERE = pathlib.Path(__file__).resolve().parent
PHOTOS = HERE / "photos-native"
OUT = HERE / "out-micro"
WORK = HERE / "work"
SHEETS = HERE / "sheets"

D = b.DOCTOR
# Second line of every caption, so it shows before the "ver mais" cut.
NOTICE = "Consulta particular, não é SUS. Por chat ou por vídeo: você escolhe."
CTA = "Agende pelo WhatsApp."
SIGN = D["clinic"] + " · " + D["name"] + " · Médico · " + D["crm"]
ER = D["emergency"].replace("|", " ")
DESC = "Consulta particular · Não é SUS"

# hook: the label on the picture and the first line of the caption (one situation, never a disease).
# photos: (letter, photo number, top of the label in px - placed where it covers no face).
SETS = [
    dict(n=1, key="mora-longe", adset="RD | 1 Mora longe",
         hook="Mora longe de um consultório?",
         title="Consulta por vídeo, de onde você estiver",
         body="A consulta médica pode ser por vídeo, de qualquer cidade do Brasil, com hora marcada. "
              "Sem estrada e sem sala de espera.",
         wa="Olá! Moro longe e quero agendar uma consulta particular.",
         photos=[("A", "023", 124), ("B", "083", 905)]),
    dict(n=2, key="sem-tempo", adset="RD | 2 Sem tempo",
         hook="Sem tempo para ir ao consultório?",
         title="Consulta por vídeo, com hora marcada",
         body="A consulta pode ser por vídeo, com hora marcada: no intervalo do trabalho ou em casa. "
              "Sem trânsito e sem sala de espera.",
         wa="Olá! Quero agendar uma consulta particular, com hora marcada.",
         photos=[("A", "013", 1090), ("B", "026", 124)]),
    dict(n=3, key="cuida-dos-pais", adset="RD | 3 Cuida dos pais",
         hook="Cuida do seu pai ou da sua mãe?",
         title="Consulta por vídeo, com a família junto",
         body="A consulta pode ser em casa, por vídeo, e você participa junto. Sem viagem e sem sala de espera.",
         wa="Olá! Quero agendar uma consulta particular para meu pai ou minha mãe.",
         photos=[("A", "020", 1065), ("B", "079", 124)]),
    dict(n=4, key="receita-venceu", adset="RD | 4 Receita venceu",
         hook="A receita venceu. De novo.",
         title="Receita digital, quando indicada",
         body="E para renovar? Trânsito, fila, sala de espera. Na " + D["clinic"] + ", a consulta é por vídeo: "
              "o médico avalia e, quando indicado, emite a receita digital.",
         wa="Olá! Quero agendar uma consulta particular.",
         photos=[("A", "047", 124), ("B", "081", 1010)]),
    dict(n=5, key="funciona", adset="RD | 5 Funciona?",
         hook="Consulta por vídeo funciona?",
         title="Consulta por vídeo é consulta de verdade",
         body="Funciona assim: você agenda pelo WhatsApp e, no horário marcado, conversa com o médico por vídeo. "
              "Ele ouve, avalia e orienta. Se for preciso um exame presencial, ele avisa.",
         wa="Olá! Quero saber como funciona a consulta particular por vídeo.",
         photos=[("A", "045", 1085), ("B", "029", 1100)]),
]

# The tag and the label look like the ones on the videos (build_video.py), so photo and video ads match.
CSS = """
*{box-sizing:border-box}
html,body{margin:0;width:1080px;height:1350px;overflow:hidden;background:#000}
.ad{position:relative;width:1080px;height:1350px;overflow:hidden;font-family:'DM Sans','Segoe UI',sans-serif;color:#fff}
.photo{position:absolute;inset:0;background-size:cover;background-position:center}
.tag{position:absolute;left:0;right:0;top:34px;text-align:center}
.tag span{display:inline-flex;border-radius:14px;overflow:hidden;box-shadow:0 6px 22px rgba(0,0,0,.5);font-weight:800;font-size:36px;line-height:1}
.tag b{background:#FFD400;color:#111;padding:16px 22px;letter-spacing:.02em}
.tag i{font-style:normal;background:#fff;color:#111;padding:16px 22px}
.cap{position:absolute;left:40px;right:40px;text-align:center}
.cap span{display:inline-block;background:#fff;color:#111;font-weight:700;font-size:50px;line-height:1.2;padding:14px 26px;border-radius:14px;box-shadow:0 6px 22px rgba(0,0,0,.35)}
.shade{position:absolute;left:0;right:0;bottom:0;height:260px;background:linear-gradient(rgba(0,0,0,0),rgba(0,0,0,.74))}
.sig{position:absolute;left:44px;right:44px;bottom:32px;display:flex;justify-content:space-between;align-items:flex-end;text-shadow:0 1px 3px rgba(0,0,0,.7)}
.n{font-weight:700;font-size:34px}
.c{font-size:24px;margin-top:4px}
.i{font-size:17px;opacity:.9;white-space:nowrap}
"""


def ads():
    """One row per picture: the set it belongs to plus its own letter, photo and label position."""
    for s in SETS:
        for letter, photo, top in s["photos"]:
            code = "%d%s" % (s["n"], letter)
            yield dict(s, code=code, photo=photo, top=top, file=code + "-" + s["key"] + ".png")


def caption(a):
    return a["hook"] + "\n" + NOTICE + "\n\n" + a["body"] + "\n\n" + CTA + "\n\n" + SIGN + "\n" + ER


def whatsapp(a):
    """The pre-filled first message; the code at the end shows which ad the chat came from."""
    return a["wa"] + " (" + a["code"] + ")"


def page(a):
    e = html.escape
    photo = PHOTOS / (a["photo"] + ".png")
    return (b.HEAD + CSS + '</style></head><body><div class="ad"><div class="photo" style="background-image:url(\''
            + photo.as_uri() + '\')"></div><div class="shade"></div>'
            + '<div class="tag"><span><b>' + e(D["tag_no"]) + "</b><i>" + e(D["tag_what"]) + "</i></span></div>"
            + '<div class="cap" style="top:%dpx"><span>' % a["top"] + e(a["hook"]) + "</span></div>"
            + '<div class="sig"><div><div class="n">' + e(D["clinic"]) + '</div><div class="c">'
            + e(D["name"] + " · " + D["line1"]) + '</div></div><div class="i">Imagem ilustrativa</div></div>'
            + "</div></body></html>")


def shot(page_file, png, width, height):
    """build_ads.shot, but a Chrome failure prints what Chrome said (the log is all there is on GitHub)."""
    try:
        b.shot(page_file, png, width, height)
    except subprocess.CalledProcessError as ex:
        print("Chrome failed:", (ex.stderr or b"").decode("utf-8", "replace")[-3000:], flush=True)
        raise
    if not png.exists():
        raise SystemExit("Chrome wrote no picture for " + png.name)


def build(only):
    done = 0
    for a in ads():
        if only and a["code"] not in only:
            continue
        if not (PHOTOS / (a["photo"] + ".png")).exists():
            print("skip (no photo):", a["code"], a["photo"])
            continue
        p = WORK / ("micro-" + a["code"] + ".html")
        p.write_text(page(a), encoding="utf-8")
        shot(p, OUT / a["file"], 1080, 1350)
        done += 1
        print("built", a["file"], flush=True)
    return done


def extras():
    e = html.escape
    rows = [a for a in ads() if (OUT / a["file"]).exists()]
    # contact sheet: the A pictures on the first row, the B pictures on the second
    order = sorted(rows, key=lambda a: (a["code"][1], a["code"][0]))
    cells = "".join('<div class="cell"><img src="' + (OUT / a["file"]).as_uri() + '"><div>' + e(a["code"] + " · " + a["hook"])
                    + "</div></div>" for a in order)
    doc = ('<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#222;font:15px Segoe UI,sans-serif;color:#fff}'
           ".g{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;padding:10px}img{width:100%;display:block}"
           '.cell div{padding:3px 2px}</style><div class="g">' + cells + "</div>")
    p = WORK / "micro-sheet.html"
    p.write_text(doc, encoding="utf-8")
    shot(p, SHEETS / "micro.png", 1400, 760)

    cards = "".join(
        '<div class="card"><a href="out-micro/' + a["file"] + '"><img loading="lazy" src="out-micro/' + a["file"] + '"></a>'
        "<b>" + e(a["code"]) + " · conjunto: " + e(a["adset"]) + "</b>"
        "<h3>Título</h3><p>" + e(a["title"]) + "</p>"
        "<h3>Texto principal</h3><p>" + e(caption(a)).replace("\n", "<br>") + "</p>"
        "<h3>Descrição</h3><p>" + e(DESC) + "</p>"
        "<h3>Mensagem pronta do WhatsApp</h3><p>" + e(whatsapp(a)) + "</p></div>"
        for a in rows)
    (HERE / "micro.html").write_text(
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Renova Doutor · um anúncio por situação</title><style>body{margin:0;padding:16px;background:#F4EFE6;color:#12312F;"
        "font:15px/1.45 'Segoe UI',sans-serif}h1{font-size:22px;margin:4px 0 16px}"
        ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}"
        ".card{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.08);padding-bottom:10px}"
        ".card img{width:100%;display:block}.card b{display:block;padding:10px 12px 0;font-size:13px;color:#1F6F5F}"
        ".card h3{margin:10px 12px 0;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:#6B7F7B}"
        ".card p{margin:2px 12px 0;font-size:14px}</style>"
        "<h1>" + e(D["clinic"]) + " · um anúncio por situação (5 conjuntos, fotos A e B)</h1><div class=\"g\">" + cards + "</div></html>",
        encoding="utf-8")

    with open(HERE / "anuncios-micro.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["conjunto", "anuncio", "arquivo", "foto", "titulo", "texto principal (legenda)", "descricao", "mensagem pronta do WhatsApp"])
        for a in ads():
            w.writerow([a["adset"], a["code"], a["file"], a["photo"] + ".png", a["title"], caption(a), DESC, whatsapp(a)])


def main():
    for d in (OUT, WORK, SHEETS):
        d.mkdir(exist_ok=True)
    only = {x.upper() for x in sys.argv[1:]}
    print(build(only), "picture(s) built")
    extras()
    return 0


if __name__ == "__main__":
    sys.exit(main())
