// Stylized dog-food bag artwork, shared by the parade and finale scenes.
// Placeholder art (no brand packaging): swap for product photos when available.
(function () {
  "use strict";

  var BRANDS = [
    { name: "Сириус", color: "#2347A8", dark: "#152E70" },
    { name: "Трендлайн", color: "#14946A", dark: "#0B5F43" },
    { name: "Дилли", color: "#E2462F", dark: "#9E2A18" },
    { name: "Пилот", color: "#7B4BD3", dark: "#4F2C9A" },
  ];

  function teethPath(x0, x1, y, count, h) {
    var step = (x1 - x0) / count;
    var d = "M" + x0 + " " + y;
    for (var k = 0; k < count; k++) {
      d += " l" + step / 2 + " " + -h + " l" + step / 2 + " " + h;
    }
    return d;
  }

  function paw(cx, cy, s, fill) {
    return (
      '<g transform="translate(' + cx + " " + cy + ") scale(" + s + ')" fill="' + fill + '">' +
      '<ellipse cx="0" cy="12" rx="26" ry="21"/>' +
      '<ellipse cx="-29" cy="-14" rx="9" ry="12" transform="rotate(-24 -29 -14)"/>' +
      '<ellipse cx="-10" cy="-30" rx="9.5" ry="13"/>' +
      '<ellipse cx="10" cy="-30" rx="9.5" ry="13"/>' +
      '<ellipse cx="29" cy="-14" rx="9" ry="12" transform="rotate(24 29 -14)"/>' +
      "</g>"
    );
  }

  function svg(brand, uid) {
    var body =
      "M44 58 C36 200 30 380 30 478 C30 510 52 524 84 524 L316 524 C348 524 370 510 370 478 C370 380 364 200 356 58 Z";
    var name = brand.name.toUpperCase();
    // Oswald caps run ~0.56em; keep the name inside the 236-unit label.
    var nameSize = Math.min(56, 236 / (name.length * 0.56));
    var sheen = "sheen-" + uid;
    return (
      '<svg viewBox="0 0 400 540" aria-hidden="true">' +
      "<defs>" +
      '<linearGradient id="' + sheen + '" x1="0" x2="1" y1="0" y2="0">' +
      '<stop offset="0" stop-color="#000" stop-opacity="0.28"/>' +
      '<stop offset="0.13" stop-color="#000" stop-opacity="0"/>' +
      '<stop offset="0.28" stop-color="#fff" stop-opacity="0.22"/>' +
      '<stop offset="0.4" stop-color="#fff" stop-opacity="0"/>' +
      '<stop offset="0.86" stop-color="#000" stop-opacity="0"/>' +
      '<stop offset="1" stop-color="#000" stop-opacity="0.3"/>' +
      "</linearGradient>" +
      "</defs>" +
      '<path d="' + body + '" fill="' + brand.color + '"/>' +
      paw(200, 452, 1.05, "rgba(255,255,255,0.16)") +
      '<path d="' + body + '" fill="url(#' + sheen + ')"/>' +
      '<path d="' + teethPath(36, 364, 30, 16, 12) + ' L364 74 Q200 84 36 74 Z" fill="' + brand.dark + '"/>' +
      '<line x1="52" y1="56" x2="348" y2="56" stroke="rgba(255,255,255,0.45)" stroke-width="3" stroke-dasharray="10 8"/>' +
      '<rect x="72" y="138" width="256" height="206" rx="28" fill="#FFFDF8"/>' +
      paw(200, 196, 0.62, brand.color) +
      '<text class="bag-name" x="200" y="290" text-anchor="middle" font-size="' + nameSize.toFixed(1) + '" fill="' + brand.dark + '">' + name + "</text>" +
      '<text class="bag-sub" x="200" y="324" text-anchor="middle" font-size="19" fill="#6B625A">КОРМ ДЛЯ СОБАК</text>' +
      "</svg>"
    );
  }

  window.HFBags = { brands: BRANDS, svg: svg };
})();
