// Hushpad 홈페이지: config.json(버전·공개 여부·다운로드 주소·저작권) 반영. 추적·분석 없음.
// 하위 언어 폴더(en/ ja/ zh/)에서도 루트의 config.json 하나를 씁니다: <html data-root="../">.
(function () {
  "use strict";
  var root = document.documentElement;
  var base = root.getAttribute("data-root") || "";
  function apply(cfg) {
    var pub = !!cfg.public;
    root.setAttribute("data-public", pub ? "true" : "false");
    document.querySelectorAll("[data-cfg]").forEach(function (el) {
      var k = el.getAttribute("data-cfg");
      // releaseDate는 공개 전 문구(언어별)가 페이지에 있으므로, 공개된 뒤에만 config 값으로 바꿉니다.
      if (k === "releaseDate" && !pub) return;
      var v = cfg[k];
      if (v !== undefined && v !== "") el.textContent = v;
    });
    document.querySelectorAll("[data-href]").forEach(function (el) {
      var v = cfg[el.getAttribute("data-href")];
      if (v) { el.setAttribute("href", v); el.removeAttribute("aria-disabled"); }
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
    var sum = document.getElementById("sha256");
    if (sum && cfg.sha256) sum.textContent = cfg.sha256;
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
