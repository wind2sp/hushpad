/* Hushpad 언어 선택 — <head>에서 바로 실행되도록 작게 유지합니다.
   - 루트(한국어) 페이지에 "처음" 들어온 방문자만 navigator.languages를 보고 /en/ /ja/ /zh/ 로 "한 번" 보냅니다.
     ko → 그대로, ja·zh·en → 해당 언어, 그 밖의 언어 → en.
   - 헤더 언어 메뉴로 고른 언어는 localStorage에 기억하고, 그 뒤로는 그 선택을 따릅니다(자동 판단 안 함).
   - 되돌이 고리 방지: 자동 이동은 루트 페이지에서만 일어나고, 이동 "전에" 기록을 남기므로 다시 일어나지 않습니다.
     하위 언어 페이지는 절대 이동시키지 않습니다. 저장소를 못 쓰면(사생활 모드 등) 아예 이동하지 않습니다.
   - 검색엔진·미리보기 봇, 사이트 안에서 이동해 온 경우에는 이동하지 않습니다. JS가 없으면 그냥 한국어 페이지입니다. */
(function () {
  'use strict';
  var d = document.documentElement;
  var KEY = 'hushpad-lang', AUTO = 'hushpad-lang-auto';
  var LANGS = { ko: 1, en: 1, ja: 1, zh: 1 };
  function get(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { window.localStorage.setItem(k, v); return get(k) === v; } catch (e) { return false; } }

  // 메뉴 클릭 = 수동 선택 기억, 메뉴 바깥 클릭·Esc = 메뉴 닫기
  document.addEventListener('click', function (e) {
    var t = e.target, a = t && t.closest ? t.closest('[data-setlang]') : null;
    if (a) set(KEY, a.getAttribute('data-setlang'));
    var open = document.querySelector('details.lang[open]');
    if (open && !(t && t.closest && t.closest('details.lang'))) open.removeAttribute('open');
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape' && e.key !== 'Esc') return;
    var open = document.querySelector('details.lang[open]');
    if (open) { open.removeAttribute('open'); var s = open.querySelector('summary'); if (s) s.focus(); }
  });

  if (d.getAttribute('data-lang') !== 'ko' || d.getAttribute('data-root') !== '') return; // 루트 페이지에서만
  if (/bot|crawl|spider|slurp|preview|scrap|facebookexternalhit|embedly|lighthouse|headless|validator/i.test(navigator.userAgent || '')) return;
  try { if (document.referrer && new URL(document.referrer).origin === location.origin) return; } catch (e) { /* 무시 */ }

  var pick = get(KEY);
  if (!LANGS[pick]) {
    if (get(AUTO)) return;                    // 이미 한 번 자동으로 정했음
    if (!set(AUTO, '1')) return;              // 기억할 수 없으면 이동하지 않음(매번 이동 방지)
    var list = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || ''];
    pick = 'en';
    for (var i = 0; i < list.length; i++) {
      var l = String(list[i]).toLowerCase().slice(0, 2);
      if (LANGS[l]) { pick = l; break; }
    }
  }
  if (pick === 'ko') return;
  var page = d.getAttribute('data-page') === 'download' ? 'download.html' : '';
  location.replace(pick + '/' + page + location.hash);
})();
