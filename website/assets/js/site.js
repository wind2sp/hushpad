// Hushpad 홈페이지: config.json(버전·공개 여부·다운로드 주소) 반영. 추적·분석 없음.
(function () {
  "use strict";
  var root = document.documentElement;
  function apply(cfg) {
    root.setAttribute("data-public", cfg.public ? "true" : "false");
    document.querySelectorAll("[data-cfg]").forEach(function (el) {
      var v = cfg[el.getAttribute("data-cfg")];
      if (v !== undefined && v !== "") el.textContent = v;
    });
    document.querySelectorAll("[data-href]").forEach(function (el) {
      var v = cfg[el.getAttribute("data-href")];
      if (v) { el.setAttribute("href", v); el.removeAttribute("aria-disabled"); }
    });
    var sum = document.getElementById("sha256");
    if (sum && cfg.sha256) sum.textContent = cfg.sha256;
  }
  fetch("config.json", { cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : {}; })
    .then(apply)
    .catch(function () { apply({ public: false }); });

  document.querySelectorAll("[data-copy]").forEach(function (b) {
    b.addEventListener("click", function () {
      var t = document.getElementById(b.getAttribute("data-copy"));
      if (!t || !navigator.clipboard) return;
      navigator.clipboard.writeText(t.textContent.trim()).then(function () {
        var o = b.textContent; b.textContent = "복사됨"; setTimeout(function () { b.textContent = o; }, 1400);
      });
    });
  });
  var y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();
})();
