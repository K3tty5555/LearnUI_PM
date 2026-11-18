/* Graphic design breakdown layers. Specimens only mark what matters
   (data-ov-type, data-ov-focus, data-ov-space, .gd-grid); this script draws the
   annotations on top so every case gets the same five layers. */
(function () {
  "use strict";
  var page = document.querySelector("[data-gd-detail]");
  if (!page) return;
  var specimen = page.querySelector(".gd-specimen");
  var buttons = Array.prototype.slice.call(page.querySelectorAll("[data-gd-layer]"));
  var notes = Array.prototype.slice.call(page.querySelectorAll("[data-gd-note]"));
  if (!specimen || !buttons.length) return;
  var palette = [];
  try { palette = JSON.parse(page.getAttribute("data-gd-palette") || "[]"); } catch (e) { palette = []; }
  var host = specimen.querySelector(".gw-poster, .gc-poster, .gs-frame, [data-gd-canvas]") || specimen;
  var layer = document.createElement("div");
  layer.className = "gd-ov-layer";
  layer.setAttribute("aria-hidden", "true");
  host.appendChild(layer);
  var on = {};

  function zh() { return document.documentElement.getAttribute("data-lang-mode") !== "en"; }
  function label(el, key) { return (zh() ? el.getAttribute("data-ov-" + key) : el.getAttribute("data-ov-" + key + "-en")) || el.getAttribute("data-ov-" + key) || ""; }
  function box(rect, base, cls, text) {
    var d = document.createElement("div");
    d.className = "gd-ov " + cls;
    d.style.left = (rect.left - base.left) + "px";
    d.style.top = (rect.top - base.top) + "px";
    d.style.width = rect.width + "px";
    d.style.height = rect.height + "px";
    if (text) { var t = document.createElement("span"); t.textContent = text; d.appendChild(t); }
    layer.appendChild(d);
    return d;
  }
  // Skip markers inside a view that is currently faded out or hidden (e.g. the inactive format of a specimen).
  function shown(el) {
    for (var n = el; n && n !== host; n = n.parentElement) {
      var cs = getComputedStyle(n);
      if (cs.display === "none" || cs.visibility === "hidden" || parseFloat(cs.opacity) < 0.1) return false;
    }
    return true;
  }
  // Positions are measured live, so formats, animation and resizing all stay in sync.
  function draw() {
    layer.innerHTML = "";
    var base = host.getBoundingClientRect();
    if (on.type) host.querySelectorAll("[data-ov-type]").forEach(function (el) {
      if (!shown(el)) return;
      var r = el.getBoundingClientRect();
      var clipped = { left: Math.max(r.left, base.left), top: Math.max(r.top, base.top), right: Math.min(r.right, base.right), bottom: Math.min(r.bottom, base.bottom) };
      if (clipped.right <= clipped.left || clipped.bottom <= clipped.top) return;
      box({ left: clipped.left, top: clipped.top, width: clipped.right - clipped.left, height: clipped.bottom - clipped.top }, base, "gd-ov-type", label(el, "type"));
    });
    if (on.focus) host.querySelectorAll("[data-ov-focus]").forEach(function (el) {
      if (!shown(el)) return;
      var r = el.getBoundingClientRect(), size = Math.min(base.width, base.height) * 0.26;
      var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      box({ left: cx - size / 2, top: cy - size / 2, width: size, height: size }, base, "gd-ov-focus", label(el, "focus"));
    });
    if (on.space) host.querySelectorAll("[data-ov-space]").forEach(function (el) {
      if (!shown(el)) return;
      box(el.getBoundingClientRect(), base, "gd-ov-space", label(el, "space"));
    });
    if (on.palette && palette.length) {
      var strip = document.createElement("div");
      strip.className = "gd-ov-palette";
      palette.forEach(function (c) { var s = document.createElement("span"); s.style.background = c.hex; s.title = c.hex; strip.appendChild(s); });
      layer.appendChild(strip);
    }
  }
  function apply() {
    buttons.forEach(function (b) {
      var k = b.getAttribute("data-gd-layer");
      b.setAttribute("aria-pressed", on[k] ? "true" : "false");
      specimen.setAttribute("data-show-" + k, on[k] ? "on" : "off");
    });
    notes.forEach(function (n) { n.hidden = !on[n.getAttribute("data-gd-note")]; });
    page.classList.toggle("gd-has-layer", Object.keys(on).some(function (k) { return on[k]; }));
    draw();
  }
  buttons.forEach(function (b) {
    b.addEventListener("click", function () {
      var k = b.getAttribute("data-gd-layer");
      if (k === "all") { var any = !buttons.every(function (x) { return x.getAttribute("data-gd-layer") === "all" || on[x.getAttribute("data-gd-layer")]; }); buttons.forEach(function (x) { var kk = x.getAttribute("data-gd-layer"); if (kk !== "all") on[kk] = any; }); }
      else on[k] = !on[k];
      apply();
    });
  });
  var pending = 0;
  function schedule() { if (pending) return; pending = requestAnimationFrame(function () { pending = 0; if (Object.keys(on).some(function (k) { return on[k]; })) draw(); }); }
  if ("ResizeObserver" in window) new ResizeObserver(schedule).observe(host);
  specimen.addEventListener("gd:layout", function () { setTimeout(draw, 540); });
  setInterval(function () { if (on.type || on.focus || on.space) draw(); }, 600);
  document.addEventListener("learnui:languagechange", draw);
  apply();
})();
