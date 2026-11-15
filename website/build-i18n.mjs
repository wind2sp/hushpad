#!/usr/bin/env node
// Hushpad 홈페이지 다국어 페이지 생성기 (Node 18+, 외부 패키지 없음)
//
//   node build-i18n.mjs          _templates/*.html + i18n/<lang>.json → 언어별 HTML 생성
//   node build-i18n.mjs --check  생성 결과가 지금 파일과 같은지만 확인 (다르면 exit 1)
//
// 출력: index.html·download.html (ko, 기본) / en/ / ja/ / zh/ 아래 같은 이름.
// 템플릿 문법:
//   {{key.path}}    번역 값 그대로(HTML 허용)
//   {{key.path|a}}  속성용 이스케이프
//   {{> name}}      _templates/partials/name.html 끼워 넣기 (머리글·바닥글 공용)
//   {{_…}}          이 스크립트가 만드는 값 (_root, _head, _langmenu, _faq …)
// 값이 배열이면 <li>…</li>로 이어 붙입니다. 번역 파일 사이에 키가 하나라도 빠지면 오류로 멈춥니다.

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(fileURLToPath(import.meta.url));
const CHECK = process.argv.includes('--check');

// 언어 목록: 첫 항목이 기본(루트) 언어입니다.
const LANGS = [
  { code: 'ko', dir: '' },
  { code: 'en', dir: 'en' },
  { code: 'ja', dir: 'ja' },
  { code: 'zh', dir: 'zh' },
];
const PAGES = ['index.html', 'download.html'];
// 실제 주소(hreflang·canonical·og:url·og:image는 절대 주소여야 검색엔진·SNS가 제대로 읽습니다).
const SITE = 'https://gdra.mycafe24.com/hushpad/';
// CSS·JS를 고치면 이 숫자를 올리고 다시 생성하세요(.htaccess가 CSS·JS를 7일 캐시하므로 ?v=로 갱신).
const ASSET_VERSION = '3';

const read = (p) => readFileSync(join(ROOT, p), 'utf8');
const dict = Object.fromEntries(LANGS.map((l) => [l.code, JSON.parse(read(`i18n/${l.code}.json`))]));

// ── 번역 키 일치 검사 ──
function shape(v, p = '', out = new Map()) {
  if (Array.isArray(v)) { out.set(p, `array:${v.length}`); v.forEach((x, i) => shape(x, `${p}[${i}]`, out)); }
  else if (v && typeof v === 'object') { for (const k of Object.keys(v)) shape(v[k], p ? `${p}.${k}` : k, out); }
  else out.set(p, typeof v);
  return out;
}
const base = shape(dict[LANGS[0].code]);
let bad = 0;
for (const { code } of LANGS.slice(1)) {
  const s = shape(dict[code]);
  for (const [k, t] of base) if (s.get(k) !== t) { console.error(`[${code}] 키 불일치: ${k} (ko=${t}, ${code}=${s.get(k) ?? '없음'})`); bad++; }
  for (const k of s.keys()) if (!base.has(k)) { console.error(`[${code}] ko에 없는 키: ${k}`); bad++; }
}
if (bad) { console.error(`번역 키 오류 ${bad}개 — 생성하지 않았습니다.`); process.exit(1); }

// ── 도우미 ──
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const get = (obj, path) => path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
// 사이트 기준 경로: ''(루트 index), 'download.html', 'en/', 'en/download.html'
const sitePath = (dir, page) => (dir ? `${dir}/` : '') + (page === 'index.html' ? '' : page);
// fromDir 페이지에서 toDir 언어의 page로 가는 상대 주소
function rel(fromDir, toDir, page) {
  const href = (fromDir ? '../' : '') + sitePath(toDir, page);
  return href || './';
}

const GLOBE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.7 5.6 3.7 9s-1.2 6.4-3.7 9c-2.5-2.6-3.7-5.6-3.7-9S9.5 5.6 12 3"/></svg>';

function render(tpl, lang, page) {
  const t = dict[lang.code];
  const root = lang.dir ? '../' : '';

  const alt = LANGS.map((l) => `<link rel="alternate" hreflang="${dict[l.code].meta.htmlLang}" href="${SITE + sitePath(l.dir, page)}">`);
  alt.push(`<link rel="alternate" hreflang="x-default" href="${SITE + sitePath('', page)}">`);
  const head = [
    `<link rel="canonical" href="${SITE + sitePath(lang.dir, page)}">`,
    ...alt,
    `<meta property="og:url" content="${SITE + sitePath(lang.dir, page)}">`,
    `<meta property="og:image" content="${SITE}assets/img/og-image.png">`,
    ...LANGS.filter((l) => l !== lang).map((l) => `<meta property="og:locale:alternate" content="${dict[l.code].meta.ogLocale}">`),
  ].join('\n');

  const menu = [
    `    <details class="lang">`,
    `      <summary aria-label="${esc(t.common.langAria)}">${GLOBE}<span>${esc(t.meta.short)}</span></summary>`,
    `      <ul>`,
    ...LANGS.map((l) => {
      const m = dict[l.code].meta;
      return `        <li><a href="${rel(lang.dir, l.dir, page)}" hreflang="${m.htmlLang}" lang="${m.htmlLang}" data-setlang="${l.code}"${l === lang ? ' aria-current="true"' : ''}>${esc(m.label)}</a></li>`;
    }),
    `      </ul>`,
    `    </details>`,
  ].join('\n');

  const faq = (t.index.faq.items || []).map((it) => `        <details><summary>${it.q}</summary><p>${it.a}</p></details>`).join('\n');

  const special = {
    _lang: lang.code, _htmlLang: t.meta.htmlLang, _ogLocale: t.meta.ogLocale, _root: root, _v: ASSET_VERSION,
    _home: page === 'index.html' ? '' : './',
    _head: head, _langmenu: menu, _faq: faq,
  };

  return tpl
    .replace(/\{\{>\s*([\w-]+)\s*\}\}/g, (_, name) => read(`_templates/partials/${name}.html`).replace(/\n$/, ''))
    .replace(/\{\{\s*([\w.]+)(\|a)?\s*\}\}/g, (_, key, attr) => {
      let v = key in special ? special[key] : get(t, key);
      if (v === undefined) throw new Error(`[${lang.code}] ${page}: 번역 키 없음 → ${key}`);
      if (Array.isArray(v)) v = v.map((x) => `<li>${x}</li>`).join('');
      return attr ? esc(v) : String(v);
    });
}

let changed = 0;
for (const page of PAGES) {
  const tpl = read(`_templates/${page}`);
  for (const lang of LANGS) {
    const html = render(tpl, lang, page);
    const left = html.match(/\{\{[^}]*\}\}/);
    if (left) throw new Error(`[${lang.code}] ${page}: 바뀌지 않은 자리 ${left[0]}`);
    const outDir = join(ROOT, lang.dir);
    const out = join(outDir, page);
    const old = existsSync(out) ? readFileSync(out, 'utf8') : null;
    if (old === html) continue;
    changed++;
    const name = (lang.dir ? lang.dir + '/' : '') + page;
    if (CHECK) { console.error(`다시 생성 필요: ${name}`); continue; }
    mkdirSync(outDir, { recursive: true });
    writeFileSync(out, html, 'utf8');
    console.log(`생성: ${name}`);
  }
}
if (CHECK && changed) { console.error('생성된 HTML이 템플릿·번역과 다릅니다. node build-i18n.mjs 를 실행하세요.'); process.exit(1); }
console.log(changed ? `완료 (${changed}개 파일)` : '변경 없음');
