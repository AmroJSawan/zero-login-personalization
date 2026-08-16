#!/usr/bin/env python3
"""Build a static site from the markdown deliverables.

No markdown library is installed and these documents are table-heavy, so this
implements the GFM subset actually used: headings, pipe tables, fenced code,
inline code, bold/italic, links, lists, blockquotes, rules.
"""

import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"

# (file, source md, page title, nav label, gallery lede)
# Page titles are names, not category labels: they have to identify the page
# in a gallery of many, so "Reference Architecture" becomes a proper noun phrase.
DOCS = [
    ("demo.html", None, "Meridian Airways", "Live Demo",
     "A fare page that reads cursor behaviour alone — gravity, returns, hesitation — and adapts in micro-steps, with a reveal layer and a freeze toggle to prove it."),
    ("signals.html", None, "Zero-Login Signal Surface", "Signal Surface",
     "Everything determinable about an anonymous visitor, computed live on your own device."),
    ("architecture.html", "ARCHITECTURE.md", "Anonymous Personalization Architecture", "Architecture",
     "The domain-agnostic POMDP formulation, the arithmetic that picks components, and how it scales."),
    ("model-selection.html", "MODEL-SELECTION.md", "Model Selection Guide", "Model Selection",
     "108 models across nine families, 76 claims adversarially verified, every number tagged."),
    ("prediction.html", "PREDICTION.md", "Anonymous Intent Prediction", "Prediction",
     "What the signals let you conclude, eight prediction targets, and the model per target."),
    ("adaptation.html", "ADAPTATION.md", "The Temporal Layer", "Adaptation",
     "What accumulating behaviour reveals, and what the evidence says about adapting in response."),
    ("models.html", "MODELS.md", "Zero-Login Model Stack", "Model Stack",
     "The feature vector and the six models that consume it, organised by time horizon."),
]

# ---------------------------------------------------------------- inline ----

def inline(text):
    spans = []

    def stash(m):
        spans.append(html.escape(m.group(1)))
        return f"\x00{len(spans)-1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                  lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{spans[int(m.group(1))]}</code>", text)
    return text


# ----------------------------------------------------------------- block ----

def is_table_sep(line):
    return bool(re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", line)) and "-" in line


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def convert(md):
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # fenced code
        if line.lstrip().startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(f"<pre><code>{html.escape(chr(10).join(buf))}</code></pre>")
            continue

        # table
        if "|" in line and i + 1 < n and is_table_sep(lines[i + 1]):
            head = split_row(line)
            aligns = []
            for c in split_row(lines[i + 1]):
                if c.startswith(":") and c.endswith(":"):
                    aligns.append("center")
                elif c.endswith(":"):
                    aligns.append("right")
                else:
                    aligns.append("left")
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(split_row(lines[i]))
                i += 1
            th = "".join(
                f'<th style="text-align:{aligns[j] if j < len(aligns) else "left"}">{inline(c)}</th>'
                for j, c in enumerate(head))
            body = ""
            for r in rows:
                tds = "".join(
                    f'<td style="text-align:{aligns[j] if j < len(aligns) else "left"}">{inline(c)}</td>'
                    for j, c in enumerate(r))
                body += f"<tr>{tds}</tr>"
            out.append(f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>')
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            txt = inline(m.group(2))
            slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", m.group(2)).lower()).strip("-")
            out.append(f'<h{lvl} id="{slug}">{txt}</h{lvl}>')
            i += 1
            continue

        # horizontal rule
        if re.match(r"^\s*(---+|\*\*\*+)\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # blockquote
        if line.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append(f"<blockquote>{inline(' '.join(buf))}</blockquote>")
            continue

        # list
        if re.match(r"^\s*([-*+]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            items = []
            while i < n and re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*+]|\d+\.)\s+", "", lines[i]))
                i += 1
                # continuation lines
                while i < n and lines[i].strip() and not re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]) \
                        and not re.match(r"^(#{1,6})\s", lines[i]) and "|" not in lines[i]:
                    items[-1] += " " + lines[i].strip()
                    i += 1
            tag = "ol" if ordered else "ul"
            lis = "".join(f"<li>{inline(x)}</li>" for x in items)
            out.append(f"<{tag}>{lis}</{tag}>")
            continue

        # blank
        if not line.strip():
            i += 1
            continue

        # paragraph
        buf = []
        while i < n and lines[i].strip() and not re.match(r"^(#{1,6})\s", lines[i]) \
                and not lines[i].lstrip().startswith("```") and not lines[i].lstrip().startswith(">") \
                and not re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]) \
                and not re.match(r"^\s*(---+|\*\*\*+)\s*$", lines[i]) \
                and not ("|" in lines[i] and i + 1 < n and is_table_sep(lines[i + 1])):
            buf.append(lines[i])
            i += 1
        if buf:
            out.append(f"<p>{inline(' '.join(buf))}</p>")

    return "\n".join(out)


# -------------------------------------------------------------- template ----

CSS = """
:root{--bg:#0b0d10;--panel:#12151a;--line:#232830;--ink:#e6e9ee;--dim:#8b95a5;
--faint:#5b6474;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--acc:#58a6ff;--acc2:#bc8cff;
--mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}
nav{position:sticky;top:0;z-index:10;background:rgba(11,13,16,.92);backdrop-filter:blur(8px);
border-bottom:1px solid var(--line);padding:10px 24px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
nav a{color:var(--dim);text-decoration:none;font-size:12px;padding:5px 10px;border-radius:6px;
font-family:var(--mono);white-space:nowrap}
nav a:hover{background:var(--panel);color:var(--ink)}
nav a.on{background:var(--panel);color:var(--acc);border:1px solid var(--line)}
nav .brand{color:var(--faint);font-size:11px;font-family:var(--mono);margin-right:10px;
text-transform:uppercase;letter-spacing:.08em}
.wrap{max-width:1080px;margin:0 auto;padding:32px 24px 100px}
h1{font-size:30px;line-height:1.2;letter-spacing:-.02em;margin:0 0 8px}
h2{font-size:21px;margin:40px 0 12px;padding-top:14px;border-top:1px solid var(--line);letter-spacing:-.01em}
h3{font-size:16px;margin:28px 0 8px;color:var(--ink)}
h4{font-size:14px;margin:20px 0 6px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}
p{margin:12px 0}
a{color:var(--acc)}
strong{color:#fff;font-weight:600}
hr{border:0;border-top:1px solid var(--line);margin:28px 0}
code{font-family:var(--mono);font-size:12.5px;background:#1a1e25;padding:1.5px 5px;
border-radius:4px;color:var(--acc2);white-space:nowrap}
pre{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px 16px;
overflow-x:auto;margin:16px 0}
pre code{background:none;padding:0;color:var(--ink);white-space:pre;font-size:12.5px}
blockquote{border-left:3px solid var(--line);margin:16px 0;padding:2px 0 2px 16px;color:var(--dim)}
ul,ol{margin:12px 0;padding-left:22px}
li{margin:5px 0}
.tw{overflow-x:auto;margin:18px 0;border:1px solid var(--line);border-radius:8px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:var(--panel);color:var(--dim);font-weight:600;font-size:11px;
text-transform:uppercase;letter-spacing:.05em;padding:9px 12px;border-bottom:1px solid var(--line);
white-space:nowrap}
td{padding:9px 12px;border-bottom:1px solid #1a1e25;vertical-align:top}
tr:last-child td{border-bottom:0}
tbody tr:hover td{background:#141821}
.lede{color:var(--dim);font-size:16px;margin:0 0 4px}
.meta{color:var(--faint);font-size:12px;font-family:var(--mono);margin-bottom:8px}
"""

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{css}</style></head><body>
<nav><span class="brand">Zero-Login Personalization</span>{nav}</nav>
<div class="wrap">{body}</div></body></html>"""


def nav_html(current):
    # Relative hrefs on purpose: root-relative paths break the moment the site is
    # served under a subpath (GitHub Pages project sites live at /repo/).
    items = ['<a href="index.html"%s>Index</a>' % (' class="on"' if current == "index" else "")]
    for fname, _, _, navlabel, _ in DOCS:
        on = ' class="on"' if fname == current else ""
        items.append(f'<a href="{fname}"{on}>{navlabel}</a>')
    return "".join(items)


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()

    # live signal page: inject the shared nav, keep its own styling intact
    src = (ROOT / "index.html").read_text()
    src = src.replace("<body>", f'<body>\n<nav style="{_navstyle()}">{nav_html("signals.html")}</nav>', 1)
    src = src.replace("</head>", f"<style>{_navcss()}</style></head>", 1)
    (SITE / "signals.html").write_text(src)

    # the demo ships verbatim: it presents as its own product, so the docs nav
    # would break the illusion. It is reachable from the index card and nav link.
    shutil.copyfile(ROOT / "demo.html", SITE / "demo.html")

    for fname, mdname, title, _, lede in DOCS:
        if mdname is None:
            continue
        md = (ROOT / mdname).read_text()
        body = convert(md)
        (SITE / fname).write_text(PAGE.format(title=title, css=CSS, nav=nav_html(fname), body=body))

    cards = "".join(
        f'<a class="card" href="{f}"><div class="ct">{t}</div><div class="cd">{d}</div></a>'
        for f, _, t, _, d in DOCS)
    index_body = f"""
<h1>Zero-Login Personalization</h1>
<p class="lede">Personalizing for a visitor with no account, no login, and no persistent identifier.
Signal surface, reference architecture, model selection, and the adaptation evidence.</p>
<div class="grid">{cards}</div>
<h2>What is here</h2>
<p>The <strong>live signal surface</strong> runs in your browser and reports what is determinable about
you right now, tagged by acquisition cost and legal class, with a running entropy meter and a
temporal ladder that climbs as you interact.</p>
<p>The <strong>reference architecture</strong> states the problem as a POMDP with episodic reset and derives
component choices from arithmetic rather than fashion, including the exact-versus-approximate
search crossover and the belief-state view that unifies every session encoder.</p>
<p>The <strong>model selection guide</strong> is the output of a twelve-agent survey: 108 models across nine
families, 76 claims adversarially verified, 29 flagged. Every number is tagged verified, corrected,
or unconfirmed, and unverified numbers are never used to justify a build decision.</p>
"""
    extra = """
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin:26px 0 10px}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:10px;
padding:16px;text-decoration:none;transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--acc);transform:translateY(-1px)}
.ct{color:var(--ink);font-weight:600;font-size:15px;margin-bottom:5px}
.cd{color:var(--dim);font-size:13px;line-height:1.5}
"""
    (SITE / "index.html").write_text(
        PAGE.format(title="Zero-Login Personalization", css=CSS + extra,
                    nav=nav_html("index"), body=index_body))

    print(f"built {len(list(SITE.glob('*.html')))} pages -> {SITE}")
    for p in sorted(SITE.glob("*.html")):
        print(f"  {p.name:24} {p.stat().st_size/1024:7.1f} KB")


def _navcss():
    return """nav{position:sticky;top:0;z-index:50;background:rgba(11,13,16,.94);
backdrop-filter:blur(8px);border-bottom:1px solid #232830;padding:10px 24px;display:flex;
gap:6px;flex-wrap:wrap;align-items:center}
nav a{color:#8b95a5;text-decoration:none;font-size:12px;padding:5px 10px;border-radius:6px;
font-family:ui-monospace,Menlo,monospace;white-space:nowrap}
nav a:hover{background:#12151a;color:#e6e9ee}
nav a.on{background:#12151a;color:#58a6ff;border:1px solid #232830}
nav .brand{color:#5b6474;font-size:11px;font-family:ui-monospace,Menlo,monospace;
margin-right:10px;text-transform:uppercase;letter-spacing:.08em}"""


def _navstyle():
    return ""


if __name__ == "__main__":
    build()
