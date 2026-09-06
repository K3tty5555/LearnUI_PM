/* UI dictionary specimens are live. Isolated frames are destroyed offscreen so
   their animation frames, timers and event listeners cannot keep running. */
(function () {
  "use strict";
  var configElement = document.getElementById("live-demo-data");
  if (!configElement) return;
  var config = JSON.parse(configElement.textContent);
  var cache = config.items;
  var requests = Object.create(null);
  var slots = Array.prototype.slice.call(document.querySelectorAll("[data-live-demo]"));
  var desired = new Set();
  var active = new Map();
  var currentMode = function () { return document.documentElement.getAttribute("data-lang-mode") || "zh"; };

  function translateFrame(translations) {
    if (document.documentElement.getAttribute("data-lang-mode") !== "zh") return;
    var words = translations.global || {};
    var patterns = (translations.patterns || []).map(function (p) { return { regex: new RegExp(p.source), target: p.target }; });
    function translated(value) {
      if (Object.prototype.hasOwnProperty.call(words, value)) return words[value];
      for (var i = 0; i < patterns.length; i++) {
        if (patterns[i].regex.test(value)) return value.replace(patterns[i].regex, patterns[i].target);
      }
      return value;
    }
    function text(node) {
      if (!node.parentElement || node.parentElement.closest("script,style")) return;
      var old = node.nodeValue || "";
      var clean = old.trim();
      if (!clean) return;
      var next = translated(clean);
      if (next !== clean) node.nodeValue = old.replace(clean, next);
    }
    function subtree(node) {
      if (node.nodeType === Node.TEXT_NODE) { text(node); return; }
      if (node.nodeType !== Node.ELEMENT_NODE || node.matches("script,style")) return;
      var walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
      var child;
      while ((child = walker.nextNode())) text(child);
      [node].concat(Array.prototype.slice.call(node.querySelectorAll("[placeholder],[title],[aria-label],[value]"))).forEach(function (element) {
        ["placeholder", "title", "aria-label", "value"].forEach(function (name) {
          if (!element.hasAttribute(name)) return;
          var value = element.getAttribute(name);
          var next = translated(value);
          if (next !== value) element.setAttribute(name, next);
        });
      });
    }
    var root = document.querySelector(".fragment");
    subtree(root);
    new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        if (mutation.type === "characterData") text(mutation.target);
        else mutation.addedNodes.forEach(subtree);
      });
    }).observe(root, { subtree: true, childList: true, characterData: true });
  }

  var frameCSS = ':root{--font-sans:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;--font-mono:ui-monospace,"SF Mono",Menlo,monospace;--bg:#f7f7f8;--bg-2:#ededf0;--fill:#e9e9ed;--line:#dddde3;--line-strong:#bcbcc5;--fg:#242428;--gray-400:#696973;--gray-500:#666670;--gray-600:#575760;--gray-700:#414148;--blue:#242428;--ease-out:cubic-bezier(.23,1,.32,1)}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:transparent}body{color:var(--fg);font:15px/1.7 var(--font-sans)}[hidden]{display:none!important}.stage-center{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:20px}.fragment{display:flex;align-items:center;justify-content:center;width:100%;height:100%;max-width:100%;pointer-events:none;user-select:none}.demo{max-width:100%}@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}';
  function documentFor(item) {
    var mode = currentMode();
    var translations = JSON.stringify(config.translations).replace(/</g, "\\u003c");
    return '<!doctype html><html lang="' + (mode === "zh" ? "zh-CN" : "en") + '" data-lang-mode="' + mode + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>' + frameCSS + '</style></head><body><div class="stage-center"><div class="fragment">' + item.html + '</div></div><script>(' + translateFrame.toString() + ')(' + translations + ');<\/script></body></html>';
  }

  function stop(slot) {
    var frame = active.get(slot);
    if (frame) frame.remove();
    active.delete(slot);
    slot.classList.remove("is-live");
    slot.dataset.liveState = "paused";
  }
  function attach(slot, item) {
    if (!desired.has(slot) || document.hidden || active.has(slot)) return;
    var frame = document.createElement("iframe");
    frame.className = "live-specimen-frame";
    frame.title = slot.getAttribute("data-live-name") || slot.dataset.liveDemo;
    frame.tabIndex = -1;
    frame.setAttribute("aria-hidden", "true");
    frame.setAttribute("sandbox", "allow-scripts");
    frame.addEventListener("load", function () {
      if (active.get(slot) !== frame) return;
      slot.classList.add("is-live");
      slot.dataset.liveState = "running";
    });
    frame.srcdoc = documentFor(item);
    active.set(slot, frame);
    slot.appendChild(frame);
  }
  function start(slot) {
    if (document.hidden || !desired.has(slot) || active.has(slot)) return;
    var slug = slot.dataset.liveDemo;
    if (cache[slug]) { attach(slot, cache[slug]); return; }
    slot.dataset.liveState = "loading";
    if (!requests[slug]) {
      requests[slug] = fetch(slot.getAttribute("data-live-source")).then(function (response) {
        if (!response.ok) throw new Error("Specimen unavailable");
        return response.json();
      }).then(function (item) {
        if (typeof item.html !== "string") throw new Error("Invalid specimen");
        cache[slug] = item;
        return item;
      }).finally(function () { delete requests[slug]; });
    }
    requests[slug].then(function (item) { attach(slot, item); }).catch(function () {
      if (!desired.has(slot)) return;
      slot.dataset.liveState = "error";
    });
  }
  function restartVisible() {
    slots.forEach(function (slot) {
      stop(slot);
      if (desired.has(slot)) start(slot);
    });
  }
  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { desired.add(entry.target); start(entry.target); }
        else { desired.delete(entry.target); stop(entry.target); }
      });
    }, { rootMargin: "100px" });
    slots.forEach(function (slot) { observer.observe(slot); });
  } else {
    var pending = false;
    var scan = function () {
      pending = false;
      slots.forEach(function (slot) {
        var rect = slot.getBoundingClientRect();
        var visible = rect.height > 0 && rect.bottom > -100 && rect.top < innerHeight + 100;
        if (visible) { desired.add(slot); start(slot); }
        else { desired.delete(slot); stop(slot); }
      });
    };
    var schedule = function () { if (!pending) { pending = true; requestAnimationFrame(scan); } };
    addEventListener("scroll", schedule, { passive: true });
    addEventListener("resize", schedule);
    document.addEventListener("input", schedule);
    document.addEventListener("click", schedule);
    scan();
  }
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) slots.forEach(stop);
    else desired.forEach(start);
  });
  document.addEventListener("learnui:languagechange", restartVisible);
  var reduced = matchMedia("(prefers-reduced-motion: reduce)");
  if (reduced.addEventListener) reduced.addEventListener("change", restartVisible);
  addEventListener("online", function () { desired.forEach(start); });
  addEventListener("pagehide", function () { slots.forEach(stop); });
  addEventListener("pageshow", function () { desired.forEach(start); });
})();
