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
  // Marks of a layer being closed fade out here, so redraws of the open layers never cut them short.
  var leaving = document.createElement("div");
  leaving.className = "gd-ov-layer gd-ov-leaving";
  leaving.setAttribute("aria-hidden", "true");
  host.appendChild(leaving);
  var on = {};
  // Signature motion "fog clears" (docs/polish-plan.md): an opened layer's marks go from clear and
  // slightly blurred to sharp, without moving, 200ms each, 40ms apart, all done within 400ms. "All"
  // lifts the layers in the order grid, type, focus, space (palette last). Closing fades out in 120ms.
  var FOG = 200, STEP = 40, CAP = 400, LEAVE = 120;
  var ORDER = ["grid", "type", "focus", "space", "palette"];
  var batches = [];  // one per click that opens layers: {t0, keys, step}
  var still = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };

  function zh() { return document.documentElement.getAttribute("data-lang-mode") !== "en"; }
  function label(el, key) { return (zh() ? el.getAttribute("data-ov-" + key) : el.getAttribute("data-ov-" + key + "-en")) || el.getAttribute("data-ov-" + key) || ""; }
  function box(rect, base, cls, text, k) {
    var d = document.createElement("div");
    d.className = "gd-ov " + cls;
    d.setAttribute("data-k", k);
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
  // Redraws (every 600ms, on resize) rebuild the marks; a mark still inside its batch's window picks
  // its animation up where it was (negative delay), so a redraw never pops it to full strength.
  function fog(marks) {
    var now = performance.now();
    batches = batches.filter(function (b) { return now - b.t0 < CAP; });
    if (still.matches) return;
    batches.forEach(function (b) {
      var i = b.keys.grid ? 1 : 0;
      var list = marks.filter(function (m) { return b.keys[m.getAttribute("data-k")]; });
      if (b.step === null) b.step = list.length + i > 1 ? Math.min(STEP, (CAP - FOG) / (list.length + i - 1)) : 0;
      list.forEach(function (m) {
        m.classList.add("is-fog");
        m.style.animationDelay = Math.round(i++ * b.step - (now - b.t0)) + "ms";
      });
    });
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
      box({ left: clipped.left, top: clipped.top, width: clipped.right - clipped.left, height: clipped.bottom - clipped.top }, base, "gd-ov-type", label(el, "type"), "type");
    });
    if (on.focus) host.querySelectorAll("[data-ov-focus]").forEach(function (el) {
      if (!shown(el)) return;
      var r = el.getBoundingClientRect(), size = Math.min(base.width, base.height) * 0.26;
      var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      box({ left: cx - size / 2, top: cy - size / 2, width: size, height: size }, base, "gd-ov-focus", label(el, "focus"), "focus");
    });
    if (on.space) host.querySelectorAll("[data-ov-space]").forEach(function (el) {
      if (!shown(el)) return;
      box(el.getBoundingClientRect(), base, "gd-ov-space", label(el, "space"), "space");
    });
    if (on.palette && palette.length) {
      var strip = document.createElement("div");
      strip.className = "gd-ov-palette";
      strip.setAttribute("data-k", "palette");
      palette.forEach(function (c) { var s = document.createElement("span"); s.style.background = c.hex; s.title = c.hex; strip.appendChild(s); });
      layer.appendChild(strip);
    }
    fog(Array.prototype.slice.call(layer.children));
  }
  // The grid is drawn by the specimen itself; set its fade inline so it follows the same timing.
  function grid(open) {
    specimen.querySelectorAll(".gd-grid").forEach(function (g) {
      g.style.transition = still.matches ? "none" : open ? "opacity " + FOG + "ms var(--ease-out)" : "opacity " + LEAVE + "ms ease-in";
    });
  }
  // Runs before `on` changes: newly opened layers form one batch, closed layers fade out together.
  function change(next) {
    var opened = {}, closed = {}, any = false;
    ORDER.forEach(function (k) {
      if (next[k] && !on[k]) { opened[k] = true; any = true; }
      if (!next[k] && on[k]) closed[k] = true;
    });
    if (opened.grid) grid(true); else if (closed.grid) grid(false);
    batches.forEach(function (b) { Object.keys(closed).forEach(function (k) { delete b.keys[k]; }); });
    if (any) batches.push({ t0: performance.now(), keys: opened, step: null });
    Array.prototype.slice.call(layer.children).forEach(function (m) {
      if (!closed[m.getAttribute("data-k")]) return;
      if (still.matches) { layer.removeChild(m); return; }
      var o = getComputedStyle(m).opacity;
      m.classList.remove("is-fog");
      m.style.animationDelay = "";
      m.style.opacity = o;
      leaving.appendChild(m);
      setTimeout(function () { if (m.parentNode) m.parentNode.removeChild(m); }, LEAVE + 40);
    });
    on = next;
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
      var k = b.getAttribute("data-gd-layer"), next = {};
      Object.keys(on).forEach(function (kk) { next[kk] = on[kk]; });
      if (k === "all") { var any = !buttons.every(function (x) { return x.getAttribute("data-gd-layer") === "all" || on[x.getAttribute("data-gd-layer")]; }); buttons.forEach(function (x) { var kk = x.getAttribute("data-gd-layer"); if (kk !== "all") next[kk] = any; }); }
      else next[k] = !on[k];
      change(next);
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
