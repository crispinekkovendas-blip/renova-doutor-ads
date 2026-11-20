"""Builds 100 telemedicine ad images (1080x1350, 4:5) for Meta.

Usage:
    python -X utf8 build_ads.py              build every ad into the out folder
    python -X utf8 build_ads.py 003 045      build only those numbers
    python -X utf8 build_ads.py --sheets     only rebuild the contact sheets and the list

Photos come from Higgsfield (photos-original folder). Every word on an ad comes from this
file, so the doctor's name and CRM are always exact. Change DOCTOR and run again.
"""
import csv
import html
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PHOTO_DIRS = [HERE / "photos-original", HERE / "photos"]
OUT = HERE / "out"
WORK = HERE / "work"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# The client's data (CFM 2.336/2023, art. 4: name, CRM with state, the word MÉDICO;
# specialty + RQE only when registered at the CRM).
# State given by the user on 2026-11-18: SP. Still unknown: whether the doctor has a
# registered specialty with an RQE number (it would go in line2).
DOCTOR = {
    "name": "Dr. Kevin Tuco Crispin",
    "crm": "CRM-SP 283659",
    "line1": "MÉDICO · CRM-SP 283659",
    "line2": "",  # e.g. "Cardiologia · RQE 00000"; leave empty when there is no RQE
    "initials": "KC",
    "clinic": "Renova Doutor",  # the clinic that provides the consultations; used by the video ads
    # Asked for by the user on 2026-11-18, so nobody taps expecting free public care. Used by the video ads.
    "tag_no": "NÃO É SUS",                  # yellow half of the tag that stays at the top of every video
    "tag_what": "CONSULTA PARTICULAR",      # white half of that tag
    "service": "Consulta particular · por chat ou por vídeo",   # signature, under the clinic name
    # The end card that closes every video ("|" is a line break):
    "gov": "nem serviço do governo",
    "offer": "Consulta particular,|por chat ou por vídeo.",
    "cta": "Agendar consulta particular",
    "cta_small": "pelo WhatsApp",
    "emergency": "Em caso de emergência, procure um|pronto-socorro ou ligue 192.",
}
CTA = "Agendar pelo WhatsApp"

PHOTOS = {
    "sofa": ("01-sofa.png", "68%"),
    "pai": ("02-pai-e-filha.png", "74%"),
    "varanda": ("03-varanda.png", "72%"),
    "intervalo": ("04-intervalo.png", "66%"),
}

CSS = """
*{box-sizing:border-box}
html,body{margin:0;width:1080px;height:1350px;overflow:hidden}
.ad{position:relative;width:1080px;height:1350px;overflow:hidden;font-family:'DM Sans','Segoe UI',sans-serif}
.cream{background:#F4EFE6;color:#12312F;--acc:#1F6F5F;--soft:#E3DACB;--mute:#2B4A47}
.green{background:#12312F;color:#F4EFE6;--acc:#8FD3B6;--soft:#1E4A45;--mute:#C9D8D2}
.sage{background:#DCE5DA;color:#12312F;--acc:#1F6F5F;--soft:#C6D3C4;--mute:#2B4A47}
.clay{background:#B4552F;color:#FFF7EF;--acc:#FFE0CC;--soft:#9C4725;--mute:#FFE9DC}
.sand{background:#E9DFCF;color:#12312F;--acc:#9A4A2B;--soft:#D9CBB6;--mute:#3B4A44}
.pad{position:absolute;left:72px;right:72px;top:76px;bottom:236px;display:flex;flex-direction:column;z-index:1}
.mid{flex:1;display:flex;flex-direction:column;justify-content:center;padding-bottom:20px}
.deco::before{content:'';position:absolute;right:-190px;top:-190px;width:560px;height:560px;border-radius:50%;background:var(--soft);opacity:.75}
.deco::after{content:'';position:absolute;left:-150px;bottom:330px;width:300px;height:300px;border-radius:50%;border:26px solid var(--soft);opacity:.6}
.kicker{font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:26px;color:var(--acc)}
h1{font-family:'Fraunces',Georgia,serif;font-weight:600;line-height:1.05;margin:0;letter-spacing:-.01em}
.sub{font-size:36px;line-height:1.32;color:var(--mute)}
.foot{position:absolute;left:40px;right:40px;bottom:40px;z-index:3}
.bar{background:#fff;color:#12312F;border-radius:28px;padding:28px 34px;display:flex;align-items:center;justify-content:space-between;gap:24px;box-shadow:0 12px 40px rgba(0,0,0,.2)}
.n{font-weight:700;font-size:35px}
.c{font-size:25px;margin-top:5px;color:#2B4A47}
.cta{background:#1FA855;color:#fff;font-weight:700;font-size:29px;padding:22px 30px;border-radius:999px;white-space:nowrap}
.ill{text-align:right;padding:0 14px 12px;font-size:18px;color:#fff;text-shadow:0 1px 4px rgba(0,0,0,.8)}
.ill.dark{color:var(--mute);text-shadow:none}

/* T1 photo, text on top */
.photo{position:absolute;inset:0;background-size:cover;background-position:center}
.scrim{position:absolute;left:0;right:0;top:0;height:600px;background:linear-gradient(#F4EFE6 0%,rgba(244,239,230,.93) 42%,rgba(244,239,230,0) 100%)}
.t1 .head{position:absolute;left:72px;right:72px;top:76px;color:#12312F}
.t1 .kicker{color:#1F6F5F}
.t1 h1{font-size:84px;margin-top:16px}
.t1 .sub{margin-top:22px;font-size:34px;max-width:860px;color:#2B4A47}

/* T2 photo above, colour block below */
.t2 .ph{position:absolute;left:0;right:0;top:0;height:760px;background-size:cover}
.t2 .blk{position:absolute;left:0;right:0;top:760px;bottom:0;padding:44px 72px 0}
.t2 h1{font-size:88px}
.t2 .sub{margin-top:20px;font-size:38px}
.t2 .tag{position:absolute;right:28px;top:716px;font-size:18px;color:#fff;text-shadow:0 1px 4px rgba(0,0,0,.8)}

/* T3 big type */
.t3 h1{margin-top:0}
.t3 .sub{margin-top:40px;max-width:900px;font-size:42px}
.rule{width:120px;height:8px;border-radius:4px;background:var(--acc);margin-top:44px}

/* T4 question and answer */
.bubble{background:var(--soft);border-radius:48px 48px 48px 8px;padding:52px 52px}
.bubble h1{font-size:88px}
.ans{margin-top:56px;font-size:46px;line-height:1.34}
.ans b{color:var(--acc)}
.lbl{font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:24px;color:var(--acc);margin-bottom:12px}

/* T5 steps, T6 checklist */
.t5 h1,.t6 h1{font-size:84px}
.steps{margin-top:56px;display:flex;flex-direction:column;gap:38px}
.step{display:flex;align-items:center;gap:32px;font-size:46px;line-height:1.2}
.num{flex:none;width:92px;height:92px;border-radius:50%;background:var(--acc);color:var(--bgc,#F4EFE6);display:flex;align-items:center;justify-content:center;font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:50px}
.green .num,.clay .num{color:#12312F}
.chk{flex:none;width:72px;height:72px;border-radius:50%;background:var(--acc);display:flex;align-items:center;justify-content:center}
.chk svg{width:38px;height:38px}
.note{margin-top:48px;font-size:30px;line-height:1.35;color:var(--mute)}

/* T7 myth and fact */
.myth{position:absolute;left:0;right:0;top:0;height:540px;padding:76px 72px 0;background:var(--soft)}
.fact{position:absolute;left:0;right:0;top:540px;bottom:0;padding:60px 72px 0}
.myth .txt{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:74px;line-height:1.1;margin-top:26px;opacity:.62}
.fact .txt{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:70px;line-height:1.1;margin-top:26px}

/* T8 chat */
.t8 h1{font-size:84px}
.chat{margin-top:48px;background:#ECE5DB;border-radius:40px;padding:40px 34px;display:flex;flex-direction:column;gap:24px;color:#12312F}
.msg{max-width:78%;padding:24px 30px;border-radius:28px;font-size:39px;line-height:1.26;box-shadow:0 2px 6px rgba(0,0,0,.08)}
.me{align-self:flex-end;background:#D6F5C8;border-bottom-right-radius:6px}
.you{align-self:flex-start;background:#fff;border-bottom-left-radius:6px}
.sim{margin-top:16px;font-size:20px;color:var(--mute)}

/* T9 note from the doctor */
.paper{position:absolute;left:78px;right:78px;top:190px;background:#FFFDF7;color:#1B2B29;border-radius:10px;padding:64px 62px 56px;transform:rotate(-1.4deg);box-shadow:0 26px 60px rgba(0,0,0,.28)}
.paper .tape{position:absolute;left:50%;top:-26px;width:190px;height:52px;margin-left:-95px;background:rgba(214,196,150,.75);transform:rotate(2deg)}
.paper .hand{font-family:'Caveat',cursive;font-weight:700;font-size:86px;line-height:1.1}
.paper .sig{font-family:'Caveat',cursive;font-weight:700;font-size:62px;margin-top:40px;color:#1F6F5F}
.t9 .kicker{position:absolute;left:72px;top:70px}

/* T10 call screen */
.t10 h1{font-size:78px;margin-top:18px}
.phone{position:absolute;left:50%;margin-left:-235px;bottom:210px;width:470px;height:640px;border-radius:56px 56px 0 0;background:#0C1F1D;border:10px solid #2A3F3C;border-bottom:none;padding:60px 30px 0;text-align:center;color:#F4EFE6;box-shadow:0 30px 70px rgba(0,0,0,.35)}
.avatar{width:190px;height:190px;border-radius:50%;margin:0 auto;background:linear-gradient(145deg,#2F8F7A,#1F6F5F);display:flex;align-items:center;justify-content:center;font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:86px;color:#fff}
.who{font-weight:700;font-size:33px;margin-top:30px}
.what{font-size:24px;margin-top:8px;color:#A9C4BC}
.live{display:inline-block;margin-top:24px;padding:10px 22px;border-radius:999px;background:#17332F;font-size:22px;color:#8FD3B6}
.ctl{display:flex;justify-content:center;gap:26px;margin-top:44px}
.ctl i{width:76px;height:76px;border-radius:50%;background:#22403B;display:block}
.ctl i.end{background:#D9483B}

/* T11 compare */
.t11 h1{font-size:82px}
table{width:100%;border-collapse:collapse;margin-top:52px;font-size:38px}
th{font-size:25px;text-transform:uppercase;letter-spacing:.1em;color:var(--acc);padding:0 0 18px;text-align:center}
th:first-child{text-align:left}
td{padding:32px 0;border-top:2px solid var(--soft);text-align:center}
td:first-child{text-align:left}
td b{color:var(--acc)}
.flow{margin-top:52px;display:flex;flex-direction:column;gap:30px}
.lane{background:var(--soft);border-radius:30px;padding:38px 40px}
.lane .t{font-weight:700;font-size:26px;letter-spacing:.1em;text-transform:uppercase;color:var(--acc)}
.lane .s{font-size:42px;line-height:1.3;margin-top:14px}
"""

CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'

def e(s):
    return html.escape(s)

def photo_uri(key):
    name = PHOTOS[key][0]
    for d in PHOTO_DIRS:
        if (d / name).exists():
            return (d / name).as_uri()
    return None

def footer(label=None, dark=False):
    line2 = '<div class="c">' + e(DOCTOR["line2"]) + "</div>" if DOCTOR["line2"].strip() else ""
    lab = ""
    if label:
        lab = '<div class="ill' + (" dark" if dark else "") + '">' + e(label) + "</div>"
    return (
        '<div class="foot">' + lab + '<div class="bar"><div><div class="n">' + e(DOCTOR["name"])
        + '</div><div class="c">' + e(DOCTOR["line1"]) + "</div>" + line2
        + '</div><div class="cta">' + e(CTA) + "</div></div></div>"
    )

def big_size(text):
    n = len(text)
    if n <= 26:
        return 128
    if n <= 40:
        return 112
    if n <= 58:
        return 98
    if n <= 80:
        return 86
    return 76

# ---------- templates ----------
def t1(a):
    return ('<div class="ad t1"><div class="photo" style="background-image:url(\'' + photo_uri(a["photo"])
            + '\')"></div><div class="scrim"></div><div class="head"><div class="kicker">' + e(a["kicker"])
            + "</div><h1>" + e(a["h"]) + '</h1><div class="sub">' + e(a["sub"]) + "</div></div>"
            + footer("Imagem ilustrativa") + "</div>")

def t2(a):
    pos = PHOTOS[a["photo"]][1]
    return ('<div class="ad t2 ' + a["theme"] + '"><div class="ph" style="background-image:url(\''
            + photo_uri(a["photo"]) + "');background-position:center " + pos + '"></div>'
            + '<div class="tag">Imagem ilustrativa</div><div class="blk"><h1>' + e(a["h"])
            + '</h1><div class="sub">' + e(a["sub"]) + "</div></div>" + footer() + "</div>")

def t3(a):
    size = a.get("size") or big_size(a["h"])
    sub = '<div class="sub">' + e(a["sub"]) + "</div>" if a.get("sub") else ""
    return ('<div class="ad t3 deco ' + a["theme"] + '"><div class="pad"><div class="kicker">' + e(a["kicker"])
            + '</div><div class="mid"><h1 style="font-size:' + str(size) + 'px">' + e(a["h"]) + '</h1><div class="rule"></div>'
            + sub + "</div></div>" + footer() + "</div>")

def t4(a):
    return ('<div class="ad t4 ' + a["theme"] + '"><div class="pad"><div class="kicker">' + e(a["kicker"])
            + '</div><div class="mid"><div class="bubble"><h1>' + e(a["h"]) + '</h1></div><div class="ans"><div class="lbl">Resposta</div>'
            + e(a["sub"]) + "</div></div></div>" + footer() + "</div>")

def t5(a):
    rows = "".join('<div class="step"><div class="num">' + str(i + 1) + "</div><div>" + e(s) + "</div></div>"
                   for i, s in enumerate(a["items"]))
    note = '<div class="note">' + e(a["note"]) + "</div>" if a.get("note") else ""
    return ('<div class="ad t5 deco ' + a["theme"] + '"><div class="pad"><div class="kicker">' + e(a["kicker"])
            + '</div><div class="mid"><h1>' + e(a["h"]) + '</h1><div class="steps">' + rows + "</div>" + note + "</div></div>"
            + footer() + "</div>")

def t6(a):
    stroke = "#12312F" if a["theme"] in ("green", "clay") else "#F4EFE6"
    icon = CHECK.replace("{c}", stroke)
    rows = "".join('<div class="step"><div class="chk">' + icon + "</div><div>" + e(s) + "</div></div>"
                   for s in a["items"])
    note = '<div class="note">' + e(a["note"]) + "</div>" if a.get("note") else ""
    return ('<div class="ad t6 deco ' + a["theme"] + '"><div class="pad"><div class="kicker">' + e(a["kicker"])
            + '</div><div class="mid"><h1>' + e(a["h"]) + '</h1><div class="steps">' + rows + "</div>" + note + "</div></div>"
            + footer() + "</div>")

def t7(a):
    return ('<div class="ad t7 ' + a["theme"] + '"><div class="myth"><div class="kicker">✕ Mito</div><div class="txt">'
            + e(a["h"]) + '</div></div><div class="fact"><div class="kicker">✓ Fato</div><div class="txt">'
            + e(a["sub"]) + "</div></div>" + footer() + "</div>")

def t8(a):
    msgs = "".join('<div class="msg ' + who + '">' + e(text) + "</div>" for who, text in a["chat"])
    return ('<div class="ad t8 ' + a["theme"] + '"><div class="pad"><div class="kicker">' + e(a["kicker"])
            + '</div><div class="mid"><h1>' + e(a["h"]) + '</h1><div class="chat">' + msgs
            + '</div><div class="sim">Simulação ilustrativa de uma conversa de agendamento.</div></div></div>'
            + footer() + "</div>")

def t9(a):
    return ('<div class="ad t9 ' + a["theme"] + '"><div class="kicker">' + e(a["kicker"])
            + '</div><div class="paper"><div class="tape"></div><div class="hand">' + e(a["h"])
            + '</div><div class="sig">' + e(DOCTOR["name"]) + "</div></div>" + footer() + "</div>")

def t10(a):
    return ('<div class="ad t10 ' + a["theme"] + '"><div class="pad"><div class="kicker">' + e(a["kicker"])
            + "</div><h1>" + e(a["h"]) + '</h1></div><div class="phone"><div class="avatar">'
            + e(DOCTOR["initials"]) + '</div><div class="who">' + e(DOCTOR["name"]) + '</div><div class="what">'
            + e("Médico · " + DOCTOR["crm"]) + '</div><div class="live">' + e(a["sub"])
            + '</div><div class="ctl"><i></i><i></i><i class="end"></i></div></div>' + footer() + "</div>")

def t11(a):
    if a.get("rows"):
        body = ("<table><tr><th></th><th>" + e(a["cols"][0]) + "</th><th>" + e(a["cols"][1]) + "</th></tr>"
                + "".join("<tr><td>" + e(r[0]) + "</td><td>" + e(r[1]) + "</td><td><b>" + e(r[2]) + "</b></td></tr>"
                          for r in a["rows"]) + "</table>")
    else:
        body = '<div class="flow">' + "".join(
            '<div class="lane"><div class="t">' + e(t) + '</div><div class="s">' + e(s) + "</div></div>"
            for t, s in a["lanes"]) + "</div>"
    note = '<div class="note">' + e(a["note"]) + "</div>" if a.get("note") else ""
    return ('<div class="ad t11 ' + a["theme"] + '"><div class="pad"><div class="kicker">' + e(a["kicker"])
            + '</div><div class="mid"><h1>' + e(a["h"]) + "</h1>" + body + note + "</div></div>" + footer() + "</div>")

TEMPLATES = {"t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6, "t7": t7, "t8": t8,
             "t9": t9, "t10": t10, "t11": t11}

V = "Consulta por vídeo"
O = "Atendimento online"
ER = "Em caso de emergência, procure o pronto-socorro ou ligue 192."

ADS = [
    # ---- T1: photo with the headline on top (16) ----
    dict(t="t1", angle="conforto", photo="sofa", kicker=V, h="Sua consulta médica, sem sair de casa.", sub="Com hora marcada, pelo celular ou computador."),
    dict(t="t1", angle="conforto", photo="sofa", kicker=O, h="Do sofá de casa, direto com o médico.", sub="Consulta por vídeo com hora marcada."),
    dict(t="t1", angle="conforto", photo="sofa", kicker=V, h="Um café, um notebook e a sua consulta em dia.", sub="Agende pelo WhatsApp e escolha o melhor horário."),
    dict(t="t1", angle="objeção", photo="sofa", kicker="Telemedicina", h="Consulta de verdade. Só não tem sala de espera.", sub="Atendimento médico por vídeo, com hora marcada."),
    dict(t="t1", angle="família", photo="pai", kicker=O, h="Seu pai não precisa viajar para se consultar.", sub="Consulta por vídeo, de onde vocês estiverem."),
    dict(t="t1", angle="família", photo="pai", kicker="Para quem cuida dos pais", h="Na consulta por vídeo, a família participa junto.", sub="Você ao lado de quem você cuida, sem deslocamento."),
    dict(t="t1", angle="família", photo="pai", kicker=O, h="Levar ao consultório ficou difícil? A consulta vai até vocês.", sub="Por vídeo, na mesa da cozinha, com hora marcada."),
    dict(t="t1", angle="tecnologia", photo="pai", kicker=V, h="Se ele faz chamada de vídeo com os netos, consegue se consultar.", sub="É simples assim. E você pode acompanhar."),
    dict(t="t1", angle="distância", photo="varanda", kicker="Para todo o Brasil", h="Mora longe do consultório? Eu atendo online.", sub="Consulta por vídeo, com o mesmo cuidado do presencial."),
    dict(t="t1", angle="distância", photo="varanda", kicker="Para todo o Brasil", h="Falta médico na sua cidade? Eu atendo por vídeo.", sub="De qualquer lugar do Brasil, com hora marcada."),
    dict(t="t1", angle="distância", photo="varanda", kicker="Interior e capital", h="A distância não precisa adiar a sua consulta.", sub="Atendimento médico por vídeo, onde você estiver."),
    dict(t="t1", angle="tecnologia", photo="varanda", kicker=V, h="Da varanda de casa, você fala com o médico.", sub="Só precisa de um celular com internet."),
    dict(t="t1", angle="rotina", photo="intervalo", kicker=V, h="Sua consulta cabe no intervalo do almoço.", sub="Sem trânsito e sem sala de espera."),
    dict(t="t1", angle="rotina", photo="intervalo", kicker="Rotina corrida", h="Sem tempo de ir ao médico? A consulta vai até você.", sub="Por vídeo, no horário que cabe no seu dia."),
    dict(t="t1", angle="rotina", photo="intervalo", kicker=O, h="Não precisa faltar ao trabalho para se consultar.", sub="Consulta por vídeo com hora marcada."),
    dict(t="t1", angle="rotina", photo="intervalo", kicker=V, h="A consulta que você vive adiando cabe na sua agenda.", sub="Por vídeo, de onde você estiver."),

    # ---- T2: photo above, colour block below (12) ----
    dict(t="t2", angle="confiança", photo="sofa", theme="green", h="Médico online, com nome e CRM.", sub="Você sabe quem vai te atender."),
    dict(t="t2", angle="conforto", photo="sofa", theme="cream", h="Consulta por vídeo, com hora marcada.", sub="Agende pelo WhatsApp."),
    dict(t="t2", angle="conforto", photo="sofa", theme="clay", h="Cuide da saúde sem sair de casa.", sub="Atendimento médico por vídeo."),
    dict(t="t2", angle="família", photo="pai", theme="cream", h="Cuidar dos pais ficou mais simples.", sub="Consulta por vídeo, com a família junto."),
    dict(t="t2", angle="família", photo="pai", theme="green", h="Sem estrada e sem espera.", sub="A consulta acontece em casa, por vídeo."),
    dict(t="t2", angle="família", photo="pai", theme="sand", h="A consulta que não depende de carona.", sub="Atendimento médico por vídeo, em casa."),
    dict(t="t2", angle="distância", photo="varanda", theme="green", h="O médico atende. A distância não importa.", sub="Consulta por vídeo para todo o Brasil."),
    dict(t="t2", angle="distância", photo="varanda", theme="clay", h="Atendimento médico por vídeo, em todo o Brasil.", sub="Com hora marcada, pelo celular."),
    dict(t="t2", angle="tecnologia", photo="varanda", theme="cream", h="Pelo celular, com hora marcada.", sub="Sua consulta médica por vídeo."),
    dict(t="t2", angle="rotina", photo="intervalo", theme="green", h="Consulta sem perder o dia de trabalho.", sub="Por vídeo, com hora marcada."),
    dict(t="t2", angle="rotina", photo="intervalo", theme="sand", h="Entre uma tarefa e outra, a sua consulta.", sub="Atendimento médico por vídeo."),
    dict(t="t2", angle="rotina", photo="intervalo", theme="cream", h="Sua saúde na agenda, sem deslocamento.", sub="Agende pelo WhatsApp."),

    # ---- T3: big type (16) ----
    dict(t="t3", angle="objeção", theme="green", kicker="Telemedicina", h="Consulta por vídeo é consulta de verdade.", sub="Com médico identificado, hora marcada e registro em prontuário."),
    dict(t="t3", angle="conforto", theme="cream", kicker=O, h="Seu médico, a uma chamada de vídeo de distância.", sub="Agende pelo WhatsApp e consulte de onde estiver."),
    dict(t="t3", angle="rotina", theme="clay", kicker=V, h="Sem trânsito. Sem sala de espera. Com hora marcada.", sub="Atendimento médico por vídeo."),
    dict(t="t3", angle="conforto", theme="sage", kicker=O, h="Você não precisa sair de casa para falar com um médico.", sub="Consulta por vídeo, pelo celular ou computador."),
    dict(t="t3", angle="confiança", theme="cream", kicker="Quem atende", h="Médico com nome, sobrenome e CRM.", sub="Na consulta por vídeo, você sabe quem está do outro lado."),
    dict(t="t3", angle="confiança", theme="green", kicker="Acompanhamento", h="O mesmo médico, a cada consulta.", sub="Atendimento por vídeo com quem já conhece o seu histórico."),
    dict(t="t3", angle="conforto", theme="sand", kicker=V, h="A consulta vai até você.", sub="Por vídeo, com hora marcada, de qualquer lugar do Brasil."),
    dict(t="t3", angle="tecnologia", theme="sage", kicker="É simples", h="Chamada de vídeo você já sabe fazer. Consulta por vídeo é igual.", sub="Só precisa de um celular com internet."),
    dict(t="t3", angle="distância", theme="green", kicker="Para todo o Brasil", h="Longe do consultório. Perto do médico.", sub="Atendimento médico por vídeo, onde você estiver."),
    dict(t="t3", angle="rotina", theme="cream", kicker=O, h="Marque hoje. Consulte de casa.", sub="O agendamento é pelo WhatsApp."),
    dict(t="t3", angle="rotina", theme="sand", kicker="Faça a conta", h="Quanto tempo você gasta para ir a uma consulta?", sub="Por vídeo, o caminho até o médico é abrir o celular."),
    dict(t="t3", angle="distância", theme="clay", kicker="Para todo o Brasil", h="Atendimento médico por vídeo, de qualquer cidade do país.", sub="Com hora marcada. Agende pelo WhatsApp."),
    dict(t="t3", angle="exames", theme="sage", kicker=V, h="Fez exames e ainda não mostrou a um médico?", sub="Na consulta por vídeo, você apresenta os resultados sem sair de casa."),
    dict(t="t3", angle="rotina", theme="green", kicker=O, h="Menos deslocamento. Mais tempo para cuidar de você.", sub="Consulta médica por vídeo, com hora marcada."),
    dict(t="t3", angle="distância", theme="cream", kicker="Interior", h="Sua dúvida de saúde não precisa esperar a próxima ida à cidade.", sub="Atendimento médico por vídeo, de onde você estiver."),
    dict(t="t3", angle="objeção", theme="sand", kicker="Regulamentada no Brasil", h="Telemedicina é medicina.", sub="Com médico identificado, sigilo e responsabilidade profissional."),

    # ---- T4: question and answer (10) ----
    dict(t="t4", angle="objeção", theme="cream", kicker="Pergunta frequente", h="Consulta por vídeo funciona?", sub="Funciona. O médico ouve você, avalia o caso e orienta os próximos passos. Se for preciso exame presencial, você é encaminhado."),
    dict(t="t4", angle="tecnologia", theme="sage", kicker="Pergunta frequente", h="Não sou bom com tecnologia. Consigo?", sub="Se você faz chamada de vídeo no celular, consegue. É o mesmo gesto, no horário marcado."),
    dict(t="t4", angle="receita", theme="green", kicker="Pergunta frequente", h="A receita vale na farmácia?", sub="A receita digital com assinatura eletrônica tem validade no Brasil. Ela é emitida quando há indicação médica."),
    dict(t="t4", angle="honestidade", theme="sand", kicker="Pergunta frequente", h="E se eu precisar de exame presencial?", sub="O médico orienta e encaminha. A consulta por vídeo não substitui o atendimento presencial quando ele é necessário."),
    dict(t="t4", angle="família", theme="cream", kicker="Pergunta frequente", h="Posso participar da consulta do meu pai?", sub="Pode. Na consulta por vídeo, quem cuida do paciente pode acompanhar a conversa."),
    dict(t="t4", angle="distância", theme="clay", kicker="Pergunta frequente", h="Moro em outra cidade. Posso agendar?", sub="Pode. O atendimento por vídeo é feito para pacientes de todo o Brasil."),
    dict(t="t4", angle="como funciona", theme="sage", kicker="Pergunta frequente", h="Como eu agendo?", sub="Pelo WhatsApp. Você escolhe o dia e o horário e recebe as orientações para a consulta."),
    dict(t="t4", angle="confiança", theme="green", kicker="Pergunta frequente", h="A consulta por vídeo é sigilosa?", sub="É. O sigilo médico vale do mesmo jeito, no consultório ou por vídeo."),
    dict(t="t4", angle="confiança", theme="cream", kicker="Pergunta frequente", h="Quem vai me atender?", sub="Dr. Kevin Tuco Crispin, médico, CRM-SP 283659. Sempre o mesmo profissional."),
    dict(t="t4", angle="honestidade", theme="sand", kicker="Pergunta frequente", h="Serve para emergências?", sub="Não. Em emergências, procure o pronto-socorro mais próximo ou ligue 192. A consulta por vídeo é para o cuidado do dia a dia."),

    # ---- T5: steps (6) ----
    dict(t="t5", angle="como funciona", theme="cream", kicker="Como funciona", h="A consulta por vídeo em 4 passos", items=["Você chama no WhatsApp", "Escolhe o dia e o horário", "Faz a consulta por vídeo", "Recebe as orientações do médico"], note=ER),
    dict(t="t5", angle="como funciona", theme="green", kicker="Primeira vez", h="Nunca fez consulta online? É assim:", items=["Mande uma mensagem no WhatsApp", "Combine o melhor horário", "No horário marcado, entre na chamada de vídeo", "Converse com o médico como no consultório"]),
    dict(t="t5", angle="como funciona", theme="sage", kicker="Simples", h="Do WhatsApp à consulta em 3 passos", items=["Mensagem no WhatsApp", "Horário marcado", "Consulta por vídeo"], note="Sem trânsito e sem sala de espera."),
    dict(t="t5", angle="tecnologia", theme="sand", kicker="O que você precisa", h="Para se consultar por vídeo, basta:", items=["Um celular ou computador", "Conexão com a internet", "Um lugar tranquilo para conversar"], note="Se tiver exames recentes, deixe à mão."),
    dict(t="t5", angle="como funciona", theme="clay", kicker="Prepare-se", h="Antes da sua consulta por vídeo", items=["Separe exames e receitas anteriores", "Anote as suas dúvidas", "Escolha um lugar silencioso", "Teste a câmera e o som"]),
    dict(t="t5", angle="como funciona", theme="cream", kicker="Passo a passo", h="Sua primeira consulta por vídeo", items=["Antes: agende pelo WhatsApp", "Durante: converse com o médico por vídeo", "Depois: siga as orientações recebidas"], note=ER),

    # ---- T6: checklists (8) ----
    dict(t="t6", angle="o que dá para fazer", theme="cream", kicker=V, h="Dá para fazer por vídeo:", items=["Conversar sobre sintomas e dúvidas", "Mostrar resultados de exames", "Acompanhar um tratamento", "Receber orientações e encaminhamentos"]),
    dict(t="t6", angle="para quem", theme="green", kicker="Para quem é", h="A consulta por vídeo ajuda quem:", items=["mora longe do consultório", "tem a rotina corrida", "cuida de um familiar", "prefere o conforto de casa"]),
    dict(t="t6", angle="confiança", theme="sage", kicker="Sem sair de casa", h="O que você tem na consulta por vídeo:", items=["Hora marcada", "Médico identificado, com CRM", "Receita digital, quando indicada", "Encaminhamento, se necessário"]),
    dict(t="t6", angle="objeção", theme="sand", kicker="Presencial ou por vídeo", h="O que não muda:", items=["O médico é o mesmo", "O sigilo é o mesmo", "A responsabilidade é a mesma"], note="O que muda é o caminho até a consulta."),
    dict(t="t6", angle="rotina", theme="clay", kicker=V, h="O que fica de fora:", items=["Trânsito", "Estacionamento", "Sala de espera"], note="O resto continua igual: você e o médico."),
    dict(t="t6", angle="como funciona", theme="cream", kicker="Dica", h="Tenha por perto na consulta por vídeo:", items=["Exames recentes", "Lista dos remédios em uso", "Suas dúvidas anotadas"]),
    dict(t="t6", angle="o que dá para fazer", theme="green", kicker=V, h="Quando a consulta por vídeo ajuda:", items=["Primeira conversa com o médico", "Acompanhamento", "Resultado de exames", "Dúvidas sobre um tratamento"], note=ER),
    dict(t="t6", angle="família", theme="sage", kicker="Para quem cuida de alguém", h="A consulta por vídeo facilita:", items=["Sem tirar o familiar de casa", "Você acompanha a consulta", "Horário combinado com a família"]),

    # ---- T7: myth and fact (8) ----
    dict(t="t7", angle="objeção", theme="cream", h="Consulta por vídeo é só uma conversa.", sub="É um ato médico regulamentado, com registro em prontuário."),
    dict(t="t7", angle="receita", theme="green", h="Médico online não pode receitar.", sub="Pode. A receita digital é emitida quando há indicação médica."),
    dict(t="t7", angle="tecnologia", theme="sage", h="É complicado para quem não entende de tecnologia.", sub="É uma chamada de vídeo, como as que você já faz com a família."),
    dict(t="t7", angle="confiança", theme="sand", h="Na internet, eu não sei quem está me atendendo.", sub="Aqui você sabe: Dr. Kevin Tuco Crispin, CRM-SP 283659."),
    dict(t="t7", angle="objeção", theme="cream", h="Por vídeo, o médico não consegue avaliar nada.", sub="Muito se avalia na conversa e nos exames. Quando é preciso examinar, o médico encaminha."),
    dict(t="t7", angle="confiança", theme="green", h="Consulta online não é sigilosa.", sub="O sigilo médico vale do mesmo jeito, no consultório ou por vídeo."),
    dict(t="t7", angle="rotina", theme="clay", h="Só vale a pena para quem mora longe.", sub="Vale também para quem não quer perder horas no trânsito."),
    dict(t="t7", angle="honestidade", theme="sage", h="Telemedicina substitui o pronto-socorro.", sub="Não substitui. Emergência é no pronto-socorro. A consulta por vídeo é para o cuidado do dia a dia."),

    # ---- T8: booking chat (6) ----
    dict(t="t8", angle="como funciona", theme="cream", kicker="Agendamento", h="Agendar é simples assim.", chat=[("me", "Oi! Queria marcar uma consulta por vídeo."), ("you", "Olá! Claro. Qual dia fica melhor para você?"), ("me", "Quinta-feira."), ("you", "Temos horário na quinta. Posso reservar?")]),
    dict(t="t8", angle="distância", theme="green", kicker="Para todo o Brasil", h="De qualquer cidade.", chat=[("me", "Moro no interior. Consigo consultar?"), ("you", "Consegue, sim. O atendimento é por vídeo, de onde você estiver."), ("me", "Que bom! Quero agendar.")]),
    dict(t="t8", angle="família", theme="sage", kicker="Para quem cuida dos pais", h="A família pode acompanhar.", chat=[("me", "A consulta é para o meu pai. Posso participar?"), ("you", "Pode, sim. Quem cuida do paciente é bem-vindo na consulta."), ("me", "Perfeito. Vamos marcar.")]),
    dict(t="t8", angle="tecnologia", theme="sand", kicker="Primeira vez", h="Nunca fez? Não tem segredo.", chat=[("me", "Nunca fiz consulta online..."), ("you", "É simples: no horário marcado, você entra na chamada de vídeo e conversa com o médico."), ("me", "Então eu consigo!")]),
    dict(t="t8", angle="exames", theme="cream", kicker="Exames", h="Leve seus exames para a conversa.", chat=[("me", "Tenho exames recentes. Posso mostrar?"), ("you", "Pode. Deixe os resultados à mão para apresentar ao médico na consulta."), ("me", "Combinado!")]),
    dict(t="t8", angle="confiança", theme="green", kicker="Quem atende", h="Você sabe quem está do outro lado.", chat=[("me", "Quem faz o atendimento?"), ("you", "Dr. Kevin Tuco Crispin, médico, CRM-SP 283659."), ("me", "Ótimo. Quero agendar.")]),

    # ---- T9: note from the doctor (6) ----
    dict(t="t9", angle="distância", theme="sage", kicker="Um recado do médico", h="Eu atendo por vídeo porque nem todo mundo consegue chegar ao consultório. Se esse é o seu caso, me chame no WhatsApp."),
    dict(t="t9", angle="rotina", theme="sand", kicker="Um recado do médico", h="Você não precisa atravessar a cidade para conversar com um médico. Eu atendo por vídeo, com hora marcada."),
    dict(t="t9", angle="confiança", theme="green", kicker="Um recado do médico", h="Toda consulta começa por ouvir. E isso eu consigo fazer por vídeo, de onde você estiver."),
    dict(t="t9", angle="honestidade", theme="cream", kicker="Um recado do médico", h="Se for preciso examinar pessoalmente, eu digo. Se der para conduzir por vídeo, você economiza a viagem."),
    dict(t="t9", angle="confiança", theme="clay", kicker="Um recado do médico", h="Meu compromisso por vídeo é o mesmo do consultório: ouvir, avaliar e orientar com responsabilidade."),
    dict(t="t9", angle="confiança", theme="sage", kicker="Um recado do médico", h="Atendo pacientes de todo o Brasil por vídeo. Meu nome e meu CRM estão aqui embaixo."),

    # ---- T10: call screen (6) ----
    dict(t="t10", angle="como funciona", theme="cream", kicker=V, h="Sua consulta começa assim.", sub="Consulta por vídeo"),
    dict(t="t10", angle="confiança", theme="sage", kicker=O, h="No horário marcado, o médico está do outro lado da tela.", sub="Hora marcada"),
    dict(t="t10", angle="tecnologia", theme="sand", kicker="É simples", h="Uma chamada de vídeo. Uma consulta médica.", sub="Consulta por vídeo"),
    dict(t="t10", angle="rotina", theme="clay", kicker=V, h="Hora marcada. Câmera ligada. Consulta em andamento.", sub="Em atendimento"),
    dict(t="t10", angle="confiança", theme="green", kicker="Quem atende", h="Do outro lado da tela, um médico com nome e CRM.", sub="Consulta por vídeo"),
    dict(t="t10", angle="conforto", theme="cream", kicker=O, h="O consultório agora cabe no seu celular.", sub="Consulta por vídeo"),

    # ---- T11: comparisons and plain statements (6) ----
    dict(t="t11", angle="objeção", theme="cream", kicker="Lado a lado", h="No consultório ou por vídeo", cols=["Consultório", "Por vídeo"], rows=[("Médico identificado", "Sim", "Sim"), ("Sigilo médico", "Sim", "Sim"), ("Receita, quando indicada", "Sim", "Sim"), ("Deslocamento", "Sim", "Não"), ("Sala de espera", "Sim", "Não")]),
    dict(t="t11", angle="rotina", theme="sage", kicker="O caminho até o médico", h="Dois jeitos de chegar à consulta", lanes=[("Ir ao consultório", "Sair de casa, trânsito, estacionamento, sala de espera, consulta, volta."), ("Consulta por vídeo", "Abrir o celular no horário marcado.")]),
    dict(t="t11", angle="objeção", theme="green", kicker="Lado a lado", h="O que a tela não muda", cols=["Consultório", "Por vídeo"], rows=[("Escuta do médico", "Sim", "Sim"), ("Registro em prontuário", "Sim", "Sim"), ("Responsabilidade médica", "Sim", "Sim"), ("Horas no trânsito", "Sim", "Não")]),
    dict(t="t3", angle="honestidade", theme="clay", kicker="Importante", h="Telemedicina não é para emergências.", sub="Em uma emergência, procure o pronto-socorro ou ligue 192. Para o cuidado do dia a dia, eu atendo por vídeo."),
    dict(t="t3", angle="honestidade", theme="cream", kicker="Com sinceridade", h="Nem tudo se conduz por vídeo. Quando for o caso, eu aviso.", sub="Se for preciso exame presencial, o encaminhamento faz parte da consulta."),
    dict(t="t6", angle="honestidade", theme="sand", kicker="Antes de agendar", h="Saiba o que esperar:", items=["Consulta por vídeo, com hora marcada", "Médico identificado, com CRM", "Encaminhamento presencial quando necessário"], note=ER),
]

HEAD = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&'
        'family=DM+Sans:wght@400;500;700&family=Caveat:wght@700&display=swap" rel="stylesheet"><style>')

def shot(page, png, width, height):
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--user-data-dir=" + str(WORK / ".chrome-profile"),
         "--window-size=%d,%d" % (width, height), "--virtual-time-budget=5000",
         "--screenshot=" + str(png), page.as_uri()],
        check=True, capture_output=True, timeout=180,
    )

def ad_id(i, a):
    return "%03d-%s" % (i + 1, a["t"])

def build(only):
    done = 0
    for i, a in enumerate(ADS):
        num = "%03d" % (i + 1)
        if only and num not in only:
            continue
        if a.get("photo") and not photo_uri(a["photo"]):
            print("skip (no photo):", num)
            continue
        page = WORK / (ad_id(i, a) + ".html")
        page.write_text(HEAD + CSS + "</style></head><body>" + TEMPLATES[a["t"]](a) + "</body></html>", encoding="utf-8")
        shot(page, OUT / (ad_id(i, a) + ".png"), 1080, 1350)
        done += 1
        print("built", ad_id(i, a), flush=True)
    return done

def sheets():
    per, cols = 12, 4
    names = [ad_id(i, a) for i, a in enumerate(ADS) if (OUT / (ad_id(i, a) + ".png")).exists()]
    for s in range(0, len(names), per):
        cells = "".join(
            '<div class="cell"><img src="' + (OUT / (n + ".png")).as_uri() + '"><div>' + n + "</div></div>"
            for n in names[s:s + per])
        doc = ('<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#222;font:16px Segoe UI,sans-serif;color:#fff}'
               ".g{display:grid;grid-template-columns:repeat(%d,1fr);gap:12px;padding:12px}img{width:100%%;display:block}"
               ".cell div{padding:4px 2px}</style><div class=\"g\">%s</div>" % (cols, cells))
        page = WORK / ("sheet-%02d.html" % (s // per + 1))
        page.write_text(doc, encoding="utf-8")
        shot(page, HERE / "sheets" / ("sheet-%02d.png" % (s // per + 1)), 1100, 1150)
        print("sheet", s // per + 1, flush=True)
    cards = "".join(
        '<a class="card" href="out/' + ad_id(i, a) + '.png"><img loading="lazy" src="out/' + ad_id(i, a)
        + '.png"><b>' + "%03d" % (i + 1) + " · " + e(a["angle"]) + "</b><span>" + e(a["h"]) + "</span></a>"
        for i, a in enumerate(ADS) if (OUT / (ad_id(i, a) + ".png")).exists())
    (HERE / "galeria.html").write_text(
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Anúncios de telemedicina</title><style>body{margin:0;padding:16px;background:#F4EFE6;color:#12312F;"
        "font:15px/1.35 'Segoe UI',sans-serif}h1{font-size:22px;margin:4px 0 16px}"
        ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:16px}"
        ".card{display:block;background:#fff;border-radius:12px;overflow:hidden;text-decoration:none;color:inherit;"
        "box-shadow:0 2px 10px rgba(0,0,0,.08)}.card img{width:100%;display:block}.card b{display:block;padding:10px 12px 0;"
        "font-size:13px;color:#1F6F5F}.card span{display:block;padding:4px 12px 12px}</style>"
        "<h1>" + e(DOCTOR["name"]) + " · anúncios de telemedicina</h1><div class=\"g\">" + cards + "</div></html>",
        encoding="utf-8")
    with open(HERE / "lista-de-anuncios.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["arquivo", "layout", "angulo", "foto", "titulo", "texto de apoio"])
        for i, a in enumerate(ADS):
            w.writerow([ad_id(i, a) + ".png", a["t"], a["angle"], a.get("photo", ""), a["h"], a.get("sub", "")])

def main():
    for d in (OUT, WORK, HERE / "sheets"):
        d.mkdir(exist_ok=True)
    args = sys.argv[1:]
    if "--sheets" not in args:
        print(build(set(args)), "ad(s) built of", len(ADS))
    sheets()
    return 0

if __name__ == "__main__":
    sys.exit(main())
