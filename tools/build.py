#!/usr/bin/env python3
"""Generate article pages and news/publication indexes from Markdown files."""
from pathlib import Path
from html import escape
from datetime import date
import re

ROOT = Path(__file__).resolve().parents[1]

def parse(path):
    raw = path.read_text(encoding='utf-8')
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', raw, re.S)
    if not match:
        raise ValueError(f'{path}: expected YAML-like --- metadata header')
    meta = {}
    for line in match.group(1).splitlines():
        if ':' not in line: raise ValueError(f'{path}: invalid metadata line: {line}')
        key, value = line.split(':', 1)
        meta[key.strip()] = value.strip().strip('"')
    for key in ('title', 'date', 'summary'):
        if not meta.get(key): raise ValueError(f'{path}: missing {key}')
    date.fromisoformat(meta['date'])
    return meta, match.group(2)

def inline(text):
    text = escape(text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', lambda m: '<a href="'+m[2]+'">'+m[1]+'</a>', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*', r'<em>\1</em>', text)
    return text

def render_md(source):
    # HTML blocks are supported for migrated articles; Markdown is used for new entries.
    blocks = re.split(r'\n\s*\n', source.strip())
    out=[]
    for block in blocks:
        block=block.strip()
        if not block: continue
        if block.startswith('<'):
            out.append(block)
        elif block.startswith('### '): out.append('<h3>'+inline(block[4:])+'</h3>')
        elif block.startswith('## '): out.append('<h2>'+inline(block[3:])+'</h2>')
        elif block.startswith('# '): out.append('<h2>'+inline(block[2:])+'</h2>')
        elif all(line.startswith('- ') for line in block.splitlines()):
            out.append('<ul>'+''.join('<li>'+inline(line[2:])+'</li>' for line in block.splitlines())+'</ul>')
        else: out.append('<p>'+inline(' '.join(block.splitlines()))+'</p>')
    return '\n'.join(out)

def frame(section, title, body, subpage=False):
    prefix='../' if subpage else ''
    nav=''.join(f'<a href="{prefix}{slug}.html"'+(' aria-current="page"' if slug==section else '')+f'>{label}</a>' for slug,label in [('about','About'),('research','Research'),('work-packages','Work packages'),('people','People'),('publications','Publications'),('news','News'),('funding','Funding')])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content=""><title>{escape(title)} | MindShift</title><link rel="stylesheet" href="{prefix}styles.css"></head><body><a class="skip" href="#main">Skip to content</a><header class="header"><div class="wrap navwrap"><a class="logo" href="{prefix}index.html" aria-label="MindShift home">Mind<span>Shift</span></a><button class="menu" aria-controls="navigation" aria-expanded="false">Menu ☰</button><nav id="navigation" aria-label="Main navigation">{nav}</nav></div></header><main id="main"><section class="pagehead"><div class="wrap"><div class="eyebrow">{escape(section.upper())}</div><h1>{escape(title)}</h1></div></section>{body}</main><footer><div class="wrap foot"><div><a class="logo" href="{prefix}index.html">Mind<span>Shift</span></a><p>Meaning Change in Mental Health Terminology and Its Impact on Human–AI Interaction</p></div><div><strong>Project</strong><p>2027–2029 · RJ P26-0179<br>University of Gothenburg</p><a href="mailto:pierluigi.cassotti@gu.se">Contact the principal investigator ↗</a></div></div></footer><script src="{prefix}script.js"></script></body></html>'''

def build(section):
    items=[]
    for path in sorted((ROOT/section).glob('*.md')):
        if path.name.startswith('_'): continue
        meta, source=parse(path)
        slug=path.stem
        category=meta.get('category','related' if section=='publications' else 'update').lower()
        body=f'<section class="section"><div class="wrap article"><p class="meta">{escape(meta["date"])}'+(f' · {escape(meta["authors"])}' if meta.get('authors') else '')+'</p>'+render_md(source)+f'<p><a href="../{section}.html">← All {section}</a></p></div></section>'
        (ROOT/section/(slug+'.html')).write_text(frame(section,meta['title'],body,True),encoding='utf-8')
        items.append((meta,slug,category))
    valid = {slug for _, slug, _ in items}
    for old_page in (ROOT/section).glob('*.html'):
        if old_page.stem not in valid:
            old_page.unlink()
    items.sort(key=lambda x:(x[0]['date'],x[1]),reverse=True)
    def cards(rows):
        if not rows: return '<p>No items have been published in this category yet.</p>'
        return '<div class="entries">'+''.join(f'<a class="entry" href="{section}/{escape(slug)}.html"><span>{escape(meta["date"])} · {escape(category.title())}</span><strong>{escape(meta["title"])}</strong><small>{escape(meta.get("authors") or meta["summary"])}</small><b>Read more →</b></a>' for meta,slug,category in rows)+'</div>'
    if section=='publications':
        project=[x for x in items if x[2] in ('mindshift','project','output')]
        related=[x for x in items if x not in project]
        content='<section class="section"><div class="wrap">'+cards(project)+'</div></section>'
        title='Publications and research outputs'
    else:
        content='<section class="section"><div class="wrap">'+cards(items)+'</div></section>'
        title='Project news'
    (ROOT/(section+'.html')).write_text(frame(section,title,content),encoding='utf-8')
    print(f'{section}: {len(items)} entries generated')

if __name__=='__main__':
    build('news'); build('publications')
