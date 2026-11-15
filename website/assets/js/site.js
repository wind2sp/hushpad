// Hushpad 홈페이지: config.json(버전·공개 여부·다운로드 파일·저작권) 반영 + 방문자 OS 표시. 추적·분석 없음.
// 하위 언어 폴더(en/ ja/ zh/)에서도 루트의 config.json 하나를 씁니다: <html data-root="../">.
(function () {
  "use strict";
  var root = document.documentElement;
  var base = root.getAttribute("data-root") || "";

  // ── 방문자 OS: <html data-os="win|mac|other"> (다운로드 페이지에서 해당 카드를 강조·앞으로)
  // Apple Silicon과 Intel Mac은 브라우저에서 확실히 구분할 수 없으므로 Mac이면 모두 "mac"으로 둡니다.
  function detectOS() {
    var p = "";
    try { p = (navigator.userAgentData && navigator.userAgentData.platform) || ""; } catch (e) { p = ""; }
    p = (p || navigator.platform || "").toLowerCase();
    var ua = (navigator.userAgent || "").toLowerCase();
    if (/iphone|ipad|ipod|android/.test(ua)) return "other";
    if (p.indexOf("win") === 0 || (!p && ua.indexOf("windows") >= 0)) return "win";
    if (p.indexOf("mac") === 0 || (!p && ua.indexOf("mac os x") >= 0)) {
      // iPadOS는 데스크톱 Safari처럼 "MacIntel"로 보고하지만 터치 지점이 있습니다.
      return navigator.maxTouchPoints > 1 ? "other" : "mac";
    }
    return "other";
  }
  root.setAttribute("data-os", detectOS());

  function setText(sel, v) {
    document.querySelectorAll(sel).forEach(function (el) { el.textContent = v; });
  }

  function apply(cfg) {
    var pub = !!cfg.public;
    root.setAttribute("data-public", pub ? "true" : "false");
    document.querySelectorAll("[data-cfg]").forEach(function (el) {
      var k = el.getAttribute("data-cfg");
      // releaseDate는 공개 전 문구(언어별)가 페이지에 있으므로, 공개된 뒤에만 config 값으로 바꿉니다.
      if (k === "releaseDate" && !pub) return;
      var v = cfg[k];
      if (typeof v === "string" && v !== "") el.textContent = v;
    });
    document.querySelectorAll("[data-href]").forEach(function (el) {
      var v = cfg[el.getAttribute("data-href")];
      if (v) { el.setAttribute("href", v); el.removeAttribute("aria-disabled"); }
    });

    // 다운로드 파일 (downloads.win / downloads.mac): 주소·파일 이름·크기·SHA-256
    var dls = cfg.downloads || {};
    Object.keys(dls).forEach(function (os) {
      var d = dls[os] || {};
      document.querySelectorAll('[data-dl="' + os + '"]').forEach(function (el) {
        if (d.url) el.setAttribute("href", d.url);
      });
      if (d.fileName) setText('[data-dl-name="' + os + '"]', d.fileName);
      setText('[data-dl-size="' + os + '"]', d.size ? " · " + d.size : "");
      if (d.sha256) {
        setText('[data-dl-sha="' + os + '"]', d.sha256);
        document.querySelectorAll('[data-copy="sha-' + os + '"]').forEach(function (b) { b.hidden = false; });
      }
    });

    // 바닥글 GitHub 링크: 공개 전에는 링크 없는 글자, 공개 후에는 repoUrl(+경로) 링크
    if (pub && cfg.repoUrl) {
      document.querySelectorAll("[data-repo]").forEach(function (el) {
        el.setAttribute("href", cfg.repoUrl.replace(/\/+$/, "") + el.getAttribute("data-repo"));
        el.setAttribute("rel", "noopener");
        var on = el.getAttribute("data-on-text");
        if (on) el.textContent = on;
      });
    }
  }
  fetch(base + "config.json", { cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : {}; })
    .then(apply)
    .catch(function () { apply({ public: false }); });

  document.querySelectorAll("[data-copy]").forEach(function (b) {
    b.addEventListener("click", function () {
      var t = document.getElementById(b.getAttribute("data-copy"));
      if (!t || !navigator.clipboard) return;
      navigator.clipboard.writeText(t.textContent.trim()).then(function () {
        var o = b.textContent; b.textContent = b.getAttribute("data-copied") || "Copied";
        setTimeout(function () { b.textContent = o; }, 1400);
      });
    });
  });
})();
