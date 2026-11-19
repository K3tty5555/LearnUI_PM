/* Learn UIUX site chrome JS */
(function () {
  "use strict";

  /* ---------- service worker (PWA) ---------- */
  var isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
  if ("serviceWorker" in navigator && location.protocol === "https:" && !isLocal) {
    window.addEventListener("load", function () {
      // The offline library is large. Warm it after the visible page has settled
      // so precaching never competes with the first useful screen.
      window.setTimeout(function () {
        navigator.serviceWorker.register("/sw.js").catch(function () {});
      }, 8000);
    });
  }

  /* Only fetch previews near the viewport, including after filtering. */
  function loadPreview(picture) {
    var image = picture.querySelector("img[data-src]");
    if (!image || image.hasAttribute("src")) return;
    var stage = picture.closest(".stage");
    image.addEventListener("load", function () { stage.classList.remove("preview-pending"); });
    image.addEventListener("error", function () {
      stage.classList.remove("preview-pending");
      picture.hidden = true;
      stage.querySelector(".stage-preview-error").hidden = false;
    });
    var source = picture.querySelector("source[data-preview-en]");
    source.srcset = source.getAttribute("data-preview-en");
    image.src = image.getAttribute("data-src");
  }
  if ("IntersectionObserver" in window) {
    var previewObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { loadPreview(entry.target); previewObserver.unobserve(entry.target); }
      });
    }, { rootMargin: "240px" });
    document.querySelectorAll("picture[data-preview]").forEach(function (picture) { previewObserver.observe(picture); });
  } else {
    document.querySelectorAll("picture[data-preview]").forEach(loadPreview);
  }

  /* ---------- language mode ---------- */
  var MODE_KEY = "ntui-lang-mode";
  // 首次访问（无本地偏好）默认中文；中英之间一键切换，无并排对照模式（2026-11-18 用户拍板移除）。
  function mode() {
    try { return localStorage.getItem(MODE_KEY) === "en" ? "en" : "zh"; } catch (e) { return "zh"; }
  }
  var demoTextState = new WeakMap();
  var demoAttrState = new WeakMap();
  var translatingDemos = false;

  function demoTranslation(slug, value) {
    var config = window.DEMO_I18N || {};
    var local = config.demos && config.demos[slug] || {};
    if (Object.prototype.hasOwnProperty.call(local, value)) return local[value];
    if (config.global && Object.prototype.hasOwnProperty.call(config.global, value)) return config.global[value];
    var patterns = config.patterns || [];
    for (var i = 0; i < patterns.length; i++) {
      var match = value.match(new RegExp(patterns[i].source));
      if (match) return value.replace(new RegExp(patterns[i].source), patterns[i].target);
    }
    return "";
  }

  function translateDemoText(node, slug, toChinese) {
    var record = demoTextState.get(node);
    if (!toChinese) {
      if (record && node.nodeValue === record.translated) node.nodeValue = record.original;
      demoTextState.delete(node);
      return;
    }
    var current = node.nodeValue || "";
    if (record && current === record.translated) return;
    var trimmed = current.trim();
    if (!trimmed) return;
    var translated = demoTranslation(slug, trimmed);
    if (!translated || translated === trimmed) return;
    var start = current.indexOf(trimmed);
    var next = current.slice(0, start) + translated + current.slice(start + trimmed.length);
    demoTextState.set(node, { original: current, translated: next });
    node.nodeValue = next;
  }

  function translateDemoAttrs(el, slug, toChinese) {
    var attrs = ["placeholder", "title", "aria-label", "value"];
    var records = demoAttrState.get(el) || {};
    attrs.forEach(function (attr) {
      if (!el.hasAttribute(attr)) return;
      var current = el.getAttribute(attr) || "";
      var record = records[attr];
      if (!toChinese) {
        if (record && current === record.translated) el.setAttribute(attr, record.original);
        delete records[attr];
        return;
      }
      if (record && current === record.translated) return;
      var translated = demoTranslation(slug, current.trim());
      if (!translated || translated === current) return;
      records[attr] = { original: current, translated: translated };
      el.setAttribute(attr, translated);
      if (attr === "value" && "value" in el && el.value === current) el.value = translated;
    });
    demoAttrState.set(el, records);
  }

  function translateDemoFragment(fragment, toChinese) {
    var slug = fragment.getAttribute("data-slug") || "";
    // Poster artwork (graphic specimens) and anything marked translate="no" keeps its original words.
    var walker = document.createTreeWalker(fragment, NodeFilter.SHOW_TEXT, { acceptNode: function (n) {
      return n.parentElement && n.parentElement.closest('[translate="no"], [data-gd-canvas]') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
    } });
    var node;
    translatingDemos = true;
    while ((node = walker.nextNode())) translateDemoText(node, slug, toChinese);
    fragment.querySelectorAll("[placeholder],[title],[aria-label],[value]").forEach(function (el) {
      if (el.closest('[translate="no"], [data-gd-canvas]')) return;
      translateDemoAttrs(el, slug, toChinese);
    });
    translatingDemos = false;
  }

  function translateDemos(m) {
    document.querySelectorAll(".fragment[data-slug]").forEach(function (fragment) {
      translateDemoFragment(fragment, m === "zh");
    });
  }

  function applyMode(m) {
    document.documentElement.setAttribute("data-lang-mode", m);
    document.querySelectorAll(".ls-btn").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-mode") === m);
    });
    document.querySelectorAll("input[data-ph-en][data-ph-zh]").forEach(function (input) {
      var ph = m === "en" ? input.getAttribute("data-ph-en") : input.getAttribute("data-ph-zh");
      input.setAttribute("placeholder", ph);
    });
    document.querySelectorAll("source[data-preview-en]").forEach(function (source) { source.media = m === "en" ? "all" : "(max-width: 0px)"; });
    translateDemos(m);
    document.dispatchEvent(new CustomEvent("learnui:languagechange", { detail: { mode: m } }));
  }
  document.querySelectorAll(".ls-btn").forEach(function (b) {
    b.addEventListener("click", function () {
      var m = b.getAttribute("data-mode");
      try { localStorage.setItem(MODE_KEY, m); } catch (e) {}
      applyMode(m);
    });
  });
  applyMode(mode());

  function updateNavCurrent() {
    document.querySelectorAll(".site-nav a").forEach(function (link) {
      var href = link.getAttribute("href") || "";
      var path = location.pathname;
      var current = (href === "/#top" && (path === "/" || path.indexOf("/web/") === 0 || path.indexOf("/macos/") === 0))
        || (href === "/sites/" && path.indexOf("/sites/") === 0)
        || (href === "/logos/" && path.indexOf("/logos/") === 0)
        || (href === "/graphics/" && path.indexOf("/graphics/") === 0)
        || (href === "/styles/" && path.indexOf("/styles/") === 0);
      link.classList.toggle("current", current);
      if (current) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  }
  updateNavCurrent();
  window.addEventListener("hashchange", updateNavCurrent);

  if (window.MutationObserver) {
    new MutationObserver(function (mutations) {
      if (translatingDemos || mode() !== "zh") return;
      var fragments = [];
      mutations.forEach(function (mutation) {
        var el = mutation.target.nodeType === 1 ? mutation.target : mutation.target.parentElement;
        var fragment = el && el.closest ? el.closest(".fragment[data-slug]") : null;
        if (fragment && fragments.indexOf(fragment) === -1) fragments.push(fragment);
      });
      fragments.forEach(function (fragment) { translateDemoFragment(fragment, true); });
    }).observe(document.body, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["placeholder", "title", "aria-label", "value"]
    });
  }

  /* ---------- keyboard: / or ⌘K focuses search, Esc clears ---------- */
  document.addEventListener("keydown", function (ev) {
    var tag = (ev.target.tagName || "").toLowerCase();
    var typing = tag === "input" || tag === "textarea" || ev.target.isContentEditable;
    if (ev.key === "/" && !typing && !document.querySelector("dialog[open]")) {
      var inputs = ["search", "style-search", "site-search", "logo-search", "graphic-search"].map(function (id) {
        return document.getElementById(id);
      }).filter(function (input) { return input && input.offsetParent !== null; });
      var inp = inputs[0];
      if (inp) { ev.preventDefault(); inp.focus(); inp.select(); }
    }
    if (ev.key === "Escape" && typing) {
      var active = document.activeElement;
      if (active && (active.id === "search" || active.id === "style-search" || active.id === "site-search" || active.id === "logo-search" || active.id === "graphic-search")) {
        if (active.value) { active.value = ""; active.dispatchEvent(new Event("input")); }
        active.blur();
      }
    }
  });

  function debounce(fn, ms) {
    var t = null;
    return function () {
      var args = arguments, self = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(self, args); }, ms);
    };
  }

  function syncURL(params) {
    if (!history.replaceState) return;
    var url = new URL(location.href);
    Object.keys(params).forEach(function (k) {
      if (params[k]) url.searchParams.set(k, params[k]);
      else url.searchParams.delete(k);
    });
    history.replaceState(null, "", url);
  }

  function highlightEl(el, q) {
    if (!el) return;
    if (!el.hasAttribute("data-orig")) el.setAttribute("data-orig", el.innerHTML);
    else el.innerHTML = el.getAttribute("data-orig");
    if (!q) return;
    var txt = el.textContent;
    var i = txt.toLowerCase().indexOf(q);
    if (i === -1) return;
    var before = txt.slice(0, i), hit = txt.slice(i, i + q.length), after = txt.slice(i + q.length);
    el.textContent = "";
    el.appendChild(document.createTextNode(before));
    var mark = document.createElement("mark");
    mark.textContent = hit;
    el.appendChild(mark);
    el.appendChild(document.createTextNode(after));
  }

  /* ---------- homepage search / tabs / surprise ---------- */
  var indexEl = document.getElementById("search-index");
  if (indexEl) {
    function setupSearch(INDEX) {
    var bySlug = {};
    INDEX.forEach(function (it) { bySlug[it.slug] = it; });
    var cards = Array.prototype.slice.call(document.querySelectorAll(".catalog-item[data-platform]"));
    var searchInput = document.getElementById("search");
    var noResult = document.getElementById("no-result");
    var countNote = document.getElementById("count-note");
    var tabBtns = Array.prototype.slice.call(document.querySelectorAll(".tab[data-filter]"));
    var state = { q: searchInput ? searchInput.value : "", platform: "all" };

    function score(item, q) {
      var s = 0;
      function has(str) { return str && str.toLowerCase().indexOf(q) !== -1; }
      if (has(item.name)) s += 100;
      if (has(item.name_zh)) s += 95;
      (item.aka || []).forEach(function (a) { if (has(a)) s += 60; });
      (item.aka_zh || []).forEach(function (a) { if (has(a)) s += 55; });
      (item.fuzzy || []).forEach(function (f) { if (has(f)) s += 40; });
      (item.fuzzy_zh || []).forEach(function (f) { if (has(f)) s += 38; });
      if (has(item.symbol)) s += 30;
      if (has(item.tagline)) s += 20;
      if (has(item.tagline_zh)) s += 18;
      return s;
    }

    function matchReason(item, q) {
      function has(str) { return str && str.toLowerCase().indexOf(q) !== -1; }
      if (has(item.name) || has(item.name_zh)) return "";
      var pools = [["aka", item.aka], ["aka", item.aka_zh], ["fuzzy", item.fuzzy], ["fuzzy", item.fuzzy_zh]];
      for (var p = 0; p < pools.length; p++) {
        var arr = pools[p][1] || [];
        for (var i = 0; i < arr.length; i++) {
          if (has(arr[i])) return pools[p][0] + ": “" + arr[i] + "”";
        }
      }
      if (has(item.symbol)) return "symbol: " + item.symbol;
      return "";
    }

    function apply() {
      var q = state.q.trim().toLowerCase();
      var visible = 0;
      cards.forEach(function (card) {
        var slug = card.getAttribute("data-slug");
        var item = bySlug[slug];
        var ok = state.platform === "all" || card.getAttribute("data-platform") === state.platform;
        if (ok && q) ok = score(item, q) > 0;
        card.style.display = ok ? "" : "none";

        // highlight + match reason
        highlightEl(card.querySelector(".card-name .lang-en"), q && ok ? q : "");
        highlightEl(card.querySelector(".card-name-zh"), q && ok ? q : "");
        highlightEl(card.querySelector(".card-symbol"), q && ok ? q : "");
        card.querySelectorAll(".card-tag").forEach(function (el) { highlightEl(el, q && ok ? q : ""); });
        var mEl = card.querySelector(".card-match");
        if (ok && q) {
          var reason = matchReason(item, q);
          if (reason) {
            if (!mEl) {
              mEl = document.createElement("p");
              mEl.className = "card-match";
              card.querySelector(".card-meta").appendChild(mEl);
            }
            mEl.textContent = reason;
            mEl.hidden = false;
          } else if (mEl) { mEl.hidden = true; }
        } else if (mEl) { mEl.hidden = true; }

        if (ok) visible++;
      });
      if (noResult) noResult.hidden = visible !== 0;
      if (countNote) {
        countNote.querySelectorAll("[data-tpl]").forEach(function (el) {
          el.textContent = el.getAttribute("data-tpl").replace("{n}", q ? visible + " / " + INDEX.length : visible);
        });
      }
    }

    var applyDebounced = debounce(apply, 80);
    var syncDebounced = debounce(function () {
      syncURL({ q: state.q.trim() || null, platform: state.platform === "all" ? null : state.platform });
    }, 200);

    if (searchInput) {
      searchInput.addEventListener("input", function () {
        state.q = searchInput.value;
        applyDebounced();
        syncDebounced();
      });
    }
    tabBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        tabBtns.forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        state.platform = btn.getAttribute("data-filter");
        apply();
        syncDebounced();
      });
    });
    // deep links ?platform=web&q=...
    var params = new URLSearchParams(location.search);
    var qp = params.get("platform");
    if (qp === "web" || qp === "macos") {
      state.platform = qp;
      tabBtns.forEach(function (b) { b.classList.toggle("active", b.getAttribute("data-filter") === qp); });
    }
    var qq = params.get("q");
    if (qq && searchInput) {
      searchInput.value = qq;
      state.q = qq;
    }
    if (qp || qq || state.q) apply();

    // no-result example chips
    document.querySelectorAll(".no-result-examples button[data-q]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (!searchInput) return;
        searchInput.value = btn.getAttribute("data-q");
        state.q = searchInput.value;
        apply();
        syncDebounced();
        searchInput.focus();
      });
    });

    var surprise = document.getElementById("surprise");
    if (surprise) {
      surprise.addEventListener("click", function () {
        var pool = INDEX.filter(function (it) {
          return state.platform === "all" || it.platform === state.platform;
        });
        var pick = pool[Math.floor(Math.random() * pool.length)];
        if (pick) location.href = pick.url;
      });
    }
    }
    var searchSource = indexEl.getAttribute("data-src");
    if (searchSource) {
      var loadSearch = function () {
        if (indexEl.dataset.loaded === "true" || indexEl.dataset.loading === "true") return;
        indexEl.dataset.loading = "true";
        fetch(searchSource).then(function (response) {
          if (!response.ok) throw new Error("search index unavailable");
          return response.json();
        }).then(function (data) { indexEl.dataset.loaded = "true"; setupSearch(data); }).catch(function () {
          delete indexEl.dataset.loading;
        });
      };
      var searchInput = document.getElementById("search");
      if (searchInput) searchInput.addEventListener("focus", loadSearch, { once: true });
      var params = new URLSearchParams(location.search);
      if (params.get("q") || params.get("platform")) loadSearch();
    } else {
      setupSearch(JSON.parse(indexEl.textContent));
    }
  }

  /* ---------- styles atlas search ---------- */
  var styleInput = document.getElementById("style-search");
  if (styleInput) {
    var sCards = Array.prototype.slice.call(document.querySelectorAll(".style-catalog-item"));
    var sNoResult = document.getElementById("style-no-result");
    var sCount = document.getElementById("style-count");
    var sApply = function () {
      var q = styleInput.value.trim().toLowerCase();
      var n = 0;
      sCards.forEach(function (c) {
        var ok = !q || (c.getAttribute("data-search") || "").indexOf(q) !== -1;
        c.style.display = ok ? "" : "none";
        if (ok) n++;
      });
      if (sNoResult) sNoResult.hidden = n !== 0;
      if (sCount) {
        sCount.querySelectorAll("[data-tpl]").forEach(function (el) {
          el.textContent = el.getAttribute("data-tpl").replace("{n}", q ? n + " / " + sCards.length : n);
        });
      }
    };
    var sApplyD = debounce(sApply, 80);
    var sSyncD = debounce(function () {
      syncURL({ q: styleInput.value.trim() || null });
    }, 200);
    styleInput.addEventListener("input", function () { sApplyD(); sSyncD(); });
    var sq = new URLSearchParams(location.search).get("q");
    if (sq) { styleInput.value = sq; sApply(); }
  }

  /* ---------- graphic design: type chips, style and search ---------- */
  var gdInput = document.getElementById("graphic-search");
  if (gdInput) {
    var gdCards = Array.prototype.slice.call(document.querySelectorAll(".graphic-item"));
    var gdChips = Array.prototype.slice.call(document.querySelectorAll("[data-gd-type]"));
    var gdStyle = document.getElementById("graphic-style");
    var gdCount = document.getElementById("graphic-count");
    var gdNone = document.getElementById("graphic-no-result");
    var gdReset = document.getElementById("graphic-reset");
    var gdParams = new URLSearchParams(location.search);
    var gdType = "";
    var applyGraphics = function () {
      var query = gdInput.value.trim().toLowerCase(), style = gdStyle ? gdStyle.value : "", shown = 0;
      gdCards.forEach(function (card) {
        var match = (!gdType || card.getAttribute("data-type") === gdType)
          && (!style || (card.getAttribute("data-styles") || "").split(" ").indexOf(style) !== -1)
          && (!query || (card.getAttribute("data-search") || "").indexOf(query) !== -1);
        card.hidden = !match; if (match) shown++;
      });
      gdChips.forEach(function (chip) { chip.setAttribute("aria-pressed", chip.getAttribute("data-gd-type") === gdType ? "true" : "false"); });
      if (gdCount) gdCount.querySelectorAll("[data-tpl]").forEach(function (el) { el.textContent = el.getAttribute("data-tpl").replace("{shown}", shown).replace("{total}", gdCards.length); });
      if (gdNone) gdNone.hidden = shown !== 0;
      if (gdReset) gdReset.hidden = !query && !style && !gdType;
    };
    var syncGraphics = function () { syncURL({ q: gdInput.value.trim() || null, type: gdType || null, style: gdStyle && gdStyle.value || null }); };
    var syncGraphicsD = debounce(syncGraphics, 200);
    gdInput.addEventListener("input", function () { applyGraphics(); syncGraphicsD(); });
    gdChips.forEach(function (chip) { chip.addEventListener("click", function () { gdType = chip.getAttribute("data-gd-type"); applyGraphics(); syncGraphics(); }); });
    if (gdStyle) gdStyle.addEventListener("change", function () { applyGraphics(); syncGraphics(); });
    if (gdReset) gdReset.addEventListener("click", function () { gdInput.value = ""; gdType = ""; if (gdStyle) { gdStyle.value = ""; gdStyle.dispatchEvent(new Event("change")); } applyGraphics(); syncGraphics(); gdInput.focus(); });
    gdInput.value = gdParams.get("q") || "";
    if (gdChips.some(function (c) { return c.getAttribute("data-gd-type") === gdParams.get("type") && !c.disabled; })) gdType = gdParams.get("type");
    if (gdStyle && Array.prototype.some.call(gdStyle.options, function (o) { return o.value === gdParams.get("style"); })) gdStyle.value = gdParams.get("style") || "";
    applyGraphics();
  }
  /* Colour swatches copy their hex value. */
  document.querySelectorAll("[data-copy-text]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var value = btn.getAttribute("data-copy-text");
      var done = function () { btn.classList.add("is-copied"); setTimeout(function () { btn.classList.remove("is-copied"); }, 1200); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(value).then(done, done); else done();
    });
  });

  /* ---------- logo atlas: type chips, use and search ---------- */
  var logoInput = document.getElementById("logo-search");
  if (logoInput) {
    var logoCards = Array.prototype.slice.call(document.querySelectorAll(".logo-item"));
    var logoChips = Array.prototype.slice.call(document.querySelectorAll("[data-logo-type]"));
    var logoUse = document.getElementById("logo-use");
    var logoCount = document.getElementById("logo-count");
    var logoNoResult = document.getElementById("logo-no-result");
    var logoReset = document.getElementById("logo-reset");
    var logoParams = new URLSearchParams(location.search);
    var logoType = "";
    var applyLogos = function () {
      var query = logoInput.value.trim().toLowerCase();
      var use = logoUse ? logoUse.value : "";
      var shown = 0;
      logoCards.forEach(function (card) {
        var match = (!logoType || card.getAttribute("data-type") === logoType)
          && (!use || card.getAttribute("data-use") === use)
          && (!query || (card.getAttribute("data-search") || "").indexOf(query) !== -1);
        card.hidden = !match;
        if (match) shown++;
      });
      logoChips.forEach(function (chip) { chip.setAttribute("aria-pressed", chip.getAttribute("data-logo-type") === logoType ? "true" : "false"); });
      if (logoCount) logoCount.querySelectorAll("[data-tpl]").forEach(function (el) {
        el.textContent = el.getAttribute("data-tpl").replace("{shown}", shown).replace("{total}", logoCards.length);
      });
      if (logoNoResult) logoNoResult.hidden = shown !== 0;
      if (logoReset) logoReset.hidden = !query && !use && !logoType;
    };
    var syncLogos = function () {
      syncURL({ q: logoInput.value.trim() || null, type: logoType || null, use: logoUse && logoUse.value || null });
    };
    var syncLogosD = debounce(syncLogos, 200);
    logoInput.addEventListener("input", function () { applyLogos(); syncLogosD(); });
    logoChips.forEach(function (chip) {
      chip.addEventListener("click", function () { logoType = chip.getAttribute("data-logo-type"); applyLogos(); syncLogos(); });
    });
    if (logoUse) logoUse.addEventListener("change", function () { applyLogos(); syncLogos(); });
    if (logoReset) logoReset.addEventListener("click", function () {
      logoInput.value = ""; logoType = ""; if (logoUse) { logoUse.value = ""; logoUse.dispatchEvent(new Event("change")); }
      applyLogos(); syncLogos(); logoInput.focus();
    });
    logoInput.value = logoParams.get("q") || "";
    if (logoChips.some(function (chip) { return chip.getAttribute("data-logo-type") === logoParams.get("type") && !chip.disabled; })) logoType = logoParams.get("type");
    if (logoUse && Array.prototype.some.call(logoUse.options, function (o) { return o.value === logoParams.get("use"); })) logoUse.value = logoParams.get("use") || "";
    applyLogos();
  }

  /* ---------- famous sites: search and category ---------- */
  var siteInput = document.getElementById("site-search");
  if (siteInput) {
    var siteCards = Array.prototype.slice.call(document.querySelectorAll(".site-reference-item"));
    var siteNoResult = document.getElementById("site-no-result");
    var siteCount = document.getElementById("site-count");
    var siteCategorySelect = document.getElementById("site-category");
    var siteVibeSelect = document.getElementById("site-vibe");
    var siteMore = document.getElementById("site-more");
    var siteMoreCount = document.getElementById("site-more-count");
    var siteReset = document.getElementById("site-reset");
    var siteParams = new URLSearchParams(location.search);
    var sitePageSize = 12;
    var siteLimit = sitePageSize;
    var siteAutoPending = false;
    var siteMoreRow = document.getElementById("site-more-row");
    var siteAutoNote = document.getElementById("site-auto-note");

    var applySites = function (resetLimit) {
      if (resetLimit) siteLimit = sitePageSize;
      var query = siteInput.value.trim().toLowerCase();
      var category = siteCategorySelect ? siteCategorySelect.value : "";
      var vibe = siteVibeSelect ? siteVibeSelect.value : "";
      var matched = [];
      siteCards.forEach(function (card) {
        var vibes = (card.getAttribute("data-vibes") || "").split(" ");
        var matches = (!category || card.getAttribute("data-cat") === category)
          && (!vibe || vibes.indexOf(vibe) !== -1)
          && (!query || (card.getAttribute("data-search") || "").indexOf(query) !== -1);
        if (matches) matched.push(card);
      });
      siteCards.forEach(function (card) { card.hidden = true; });
      matched.slice(0, siteLimit).forEach(function (card) { card.hidden = false; });
      var shown = Math.min(siteLimit, matched.length);
      if (siteNoResult) siteNoResult.hidden = matched.length !== 0;
      if (siteCount) {
        siteCount.querySelectorAll("[data-tpl]").forEach(function (el) {
          el.textContent = el.getAttribute("data-tpl").replace("{shown}", shown).replace("{total}", matched.length);
        });
      }
      if (siteMore) siteMore.parentElement.hidden = shown >= matched.length;
      if (siteMoreCount) siteMoreCount.textContent = shown < matched.length ? "+" + Math.min(sitePageSize, matched.length - shown) : "";
      if (siteAutoNote) siteAutoNote.hidden = shown >= matched.length || matched.length === 0;
      if (siteReset) siteReset.hidden = !query && !category && !vibe;
    };
    var applySitesD = debounce(applySites, 80);
    var syncSitesD = debounce(function () {
      syncURL({
        q: siteInput.value.trim() || null,
        category: siteCategorySelect && siteCategorySelect.value || null,
        vibe: siteVibeSelect && siteVibeSelect.value || null
      });
    }, 200);
    siteInput.addEventListener("input", function () { applySitesD(true); syncSitesD(); });
    [siteCategorySelect, siteVibeSelect].forEach(function (select) {
      if (!select) return;
      select.addEventListener("change", function () { applySites(true); syncSitesD(); });
    });
    function loadNextSites() {
      if (siteAutoPending || !siteMore || siteMore.parentElement.hidden) return;
      siteAutoPending = true;
      if (siteAutoNote) siteAutoNote.textContent = mode() === "en" ? "Loading more…" : "正在加载更多…";
      siteLimit += sitePageSize;
      applySites(false);
      window.setTimeout(function () {
        siteAutoPending = false;
        if (siteAutoNote) siteAutoNote.textContent = mode() === "en" ? "Scroll to load more automatically" : "向下滚动，自动加载更多";
      }, 120);
    }
    if (siteMore) siteMore.addEventListener("click", loadNextSites);
    if (siteMoreRow && "IntersectionObserver" in window) {
      var siteLoaderObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) { if (entry.isIntersecting) loadNextSites(); });
      }, { rootMargin: "0px 0px 420px 0px" });
      siteLoaderObserver.observe(siteMoreRow);
    } else if (siteMoreRow) {
      window.addEventListener("scroll", debounce(function () {
        if (siteMoreRow.getBoundingClientRect().top < innerHeight + 420) loadNextSites();
      }, 120), { passive: true });
    }
    if (siteReset) siteReset.addEventListener("click", function () {
      siteInput.value = "";
      if (siteCategorySelect) { siteCategorySelect.value = ""; siteCategorySelect.dispatchEvent(new Event("change")); }
      if (siteVibeSelect) { siteVibeSelect.value = ""; siteVibeSelect.dispatchEvent(new Event("change")); }
      applySites(true);
      syncURL({ q: null, category: null, vibe: null });
      siteInput.focus();
    });
    siteInput.value = siteParams.get("q") || "";
    if (siteCategorySelect && Array.prototype.some.call(siteCategorySelect.options, function (option) { return option.value === siteParams.get("category"); })) siteCategorySelect.value = siteParams.get("category") || "";
    if (siteVibeSelect && Array.prototype.some.call(siteVibeSelect.options, function (option) { return option.value === siteParams.get("vibe"); })) siteVibeSelect.value = siteParams.get("vibe") || "";
    applySites(false);
  }


  /* ---------- cross-catalog selection and export ---------- */
  var selectionKey = "learnui-selection-v1";
  var selectionDialog = document.getElementById("selection-dialog");
  var selectionDock = document.getElementById("selection-dock");
  var selectionCount = document.getElementById("selection-count");
  var selectionList = document.getElementById("selection-list");
  var selectionEmpty = document.getElementById("selection-empty");
  var selectionStatus = document.getElementById("selection-status");
  var catalog = null;
  var catalogFailed = false;
  var catalogById = {};

  function loadSelection() {
    try {
      var parsed = JSON.parse(localStorage.getItem(selectionKey) || "[]");
      return Array.isArray(parsed) ? parsed.filter(function (id) { return typeof id === "string"; }) : [];
    } catch (e) { return []; }
  }
  var selectedIds = loadSelection();

  function saveSelection() {
    try { localStorage.setItem(selectionKey, JSON.stringify(selectedIds)); } catch (e) {}
  }

  function selectedItems() {
    return selectedIds.map(function (id) { return catalogById[id]; }).filter(Boolean);
  }

  function setSelectionStatus(message) {
    if (!selectionStatus) return;
    selectionStatus.textContent = message;
    setTimeout(function () { if (selectionStatus.textContent === message) selectionStatus.textContent = ""; }, 1800);
  }

  function refreshSelectionButtons() {
    document.querySelectorAll("[data-select-id]").forEach(function (button) {
      var active = selectedIds.indexOf(button.getAttribute("data-select-id")) !== -1;
      button.classList.toggle("selected", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
      button.setAttribute("aria-label", (active ? "移除参考：" : "加入参考：") + ((catalogById[button.getAttribute("data-select-id")] || {}).nameZh || button.getAttribute("data-select-id")));
      var label = button.querySelector("[data-select-label]");
      if (label) label.textContent = active ? "已加入" : "加入参考";
    });
  }

  function renderSelection() {
    if (!selectionList) return;
    if (!catalog) {
      refreshSelectionButtons();
      document.querySelectorAll("[data-selection-total]").forEach(function (el) { el.textContent = selectedIds.length; });
      selectionDock.hidden = !selectedIds.length;
      selectionCount.textContent = selectedIds.length;
      selectionEmpty.hidden = !!selectedIds.length;
      return;
    }
    var items = selectedItems();
    selectionList.textContent = "";
    items.forEach(function (item) {
      var row = document.createElement("div");
      row.className = "selection-row";
      var link = document.createElement("a");
      link.href = item.url;
      link.textContent = item.nameZh + (item.name && item.name !== item.nameZh ? " / " + item.name : "");
      var type = document.createElement("span");
      type.textContent = item.type === "site-reference" ? "知名网站设计规范" : item.type === "logo-reference" ? "Logo 图鉴" : item.type === "graphic-reference" ? "平面设计" : item.type === "ui-element" ? "UI 元素" : "视觉风格";
      var remove = document.createElement("button");
      remove.type = "button";
      remove.className = "icon-button";
      remove.setAttribute("aria-label", "移除 " + item.nameZh);
      remove.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6"/></svg>';
      remove.addEventListener("click", function () {
        selectedIds = selectedIds.filter(function (id) { return id !== item.id; });
        saveSelection();
        renderSelection();
      });
      var text = document.createElement("div");
      text.appendChild(link);
      text.appendChild(type);
      row.appendChild(text);
      row.appendChild(remove);
      selectionList.appendChild(row);
    });
    selectionEmpty.hidden = items.length !== 0;
    selectionDock.hidden = items.length === 0;
    selectionCount.textContent = items.length;
    document.querySelectorAll("[data-selection-total]").forEach(function (el) { el.textContent = selectedIds.length; });
    ["selection-copy-md", "selection-download-json"].forEach(function (id) { document.getElementById(id).disabled = !items.length; });
    refreshSelectionButtons();
  }

  function exportPayload() {
    var items = selectedItems();
    return {
      schemaVersion: 1,
      language: "zh-CN",
      purpose: "用于 AI 原型生成的 UI 参考说明",
      projectBrief: document.getElementById("collection-brief").value.trim(),
      items: items,
      combinedGuidance: {
        structures: items.reduce(function (all, item) { return all.concat(item.structure || []); }, []),
        visualTraits: items.reduce(function (all, item) { return all.concat(item.visualTraits || []); }, []),
        prompts: items.map(function (item) { return item.prompt; }).filter(Boolean)
      }
    };
  }

  function exportMarkdown() {
    var lines = ["# UI 参考说明", "", "请结合以下参考生成原型。优先遵守页面结构、关键状态和视觉约束，不要机械复制单个示例。", ""];
    var brief = document.getElementById("collection-brief").value.trim();
    if (brief) lines.push("## 项目目标", "", brief, "");
    selectedItems().forEach(function (item) {
      lines.push("## " + item.nameZh + (item.name ? " (" + item.name + ")" : ""), "");
      lines.push("- 类型：" + (item.type === "site-reference" ? "知名网站设计规范" : item.type === "logo-reference" ? "Logo 图鉴" : item.type === "graphic-reference" ? "平面设计" : item.type === "ui-element" ? "UI 元素" : "视觉风格"));
      lines.push("- 链接：" + location.origin + item.url);
      if (item.summary) lines.push("- 说明：" + item.summary);
      if (item.prompt) lines.push("", item.prompt);
      lines.push("");
    });
    return lines.join("\n");
  }

  document.querySelectorAll("[data-select-id]").forEach(function (button) {
    button.addEventListener("click", function () {
      var id = button.getAttribute("data-select-id");
      var index = selectedIds.indexOf(id);
      if (index === -1) selectedIds.push(id);
      else selectedIds.splice(index, 1);
      saveSelection();
      refreshSelectionButtons();
      document.querySelectorAll("[data-selection-total]").forEach(function (el) { el.textContent = selectedIds.length; });
      selectionDock.hidden = !selectedIds.length;
      selectionCount.textContent = selectedIds.length;
      if (catalog) renderSelection();
    });
  });

  if (selectionDialog) {
    document.getElementById("selection-open").addEventListener("click", function () {
      if (selectionDialog.showModal) selectionDialog.showModal();
      else selectionDialog.setAttribute("open", "");
      ensureCatalog();
    });
    document.getElementById("selection-close").addEventListener("click", function () { selectionDialog.close(); });
    selectionDialog.addEventListener("click", function (event) {
      if (event.target === selectionDialog) selectionDialog.close();
    });
    document.getElementById("selection-clear").addEventListener("click", function () {
      selectedIds = [];
      saveSelection();
      renderSelection();
      setSelectionStatus("选择集已清空");
    });
    document.getElementById("selection-copy-md").addEventListener("click", function () {
      copyText(exportMarkdown()).then(function () { setSelectionStatus("Markdown 已复制，可以粘贴给 AI 了。"); }).catch(function () { setSelectionStatus("复制失败，请重试或下载 JSON。"); });
    });
    document.getElementById("selection-download-json").addEventListener("click", function () {
      var blob = new Blob([JSON.stringify(exportPayload(), null, 2)], { type: "application/json;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var link = document.createElement("a");
      link.href = url;
      link.download = "learnui-reference.json";
      link.click();
      URL.revokeObjectURL(url);
      setSelectionStatus("JSON 已下载");
    });
  }

  var catalogPromise = null;
  function ensureCatalog() {
    if (catalog) return Promise.resolve(catalog);
    if (catalogPromise) return catalogPromise;
    catalogFailed = false;
    if (globalDialog && globalDialog.open) globalSearch();
    if (selectionDialog.open && selectedIds.length) {
      selectionEmpty.hidden = true;
      selectionStatus.textContent = "正在读取你的参考…";
    }
    catalogPromise = fetch("/api/catalog.json").then(function (response) {
      if (!response.ok) throw new Error("catalog unavailable");
      return response.json();
    }).then(function (data) {
      catalog = data;
      data.items.forEach(function (item) { catalogById[item.id] = item; });
      selectedIds = selectedIds.filter(function (id) { return Boolean(catalogById[id]); });
      saveSelection();
      renderSelection();
      if (globalDialog.open) globalSearch();
      selectionStatus.textContent = "";
      return data;
    }).catch(function () {
      catalogPromise = null;
      catalogFailed = true;
      if (globalDialog.open) globalSearch();
      selectionStatus.textContent = "参考库加载失败，请关闭后重新打开重试。";
      return null;
    });
    return catalogPromise;
  }
  refreshSelectionButtons();
  document.querySelectorAll("[data-selection-total]").forEach(function (el) { el.textContent = selectedIds.length; });
  selectionDock.hidden = !selectedIds.length;
  selectionCount.textContent = selectedIds.length;

  /* ---------- collection context and global command search ---------- */
  function copyText(value) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(value);
    return new Promise(function (resolve, reject) {
      var input = document.createElement("textarea");
      input.value = value;
      input.style.cssText = "position:fixed;opacity:0;left:0;top:0";
      (document.querySelector("dialog[open]") || document.body).appendChild(input);
      input.select();
      var ok = document.execCommand("copy");
      input.remove();
      if (ok) resolve(); else reject(new Error("Clipboard unavailable"));
    });
  }
  var projectBrief = document.getElementById("collection-brief");
  try { projectBrief.value = localStorage.getItem("learnui-project-brief") || ""; } catch (e) {}
  projectBrief.addEventListener("input", function () {
    try { localStorage.setItem("learnui-project-brief", projectBrief.value); } catch (e) {}
  });
  document.querySelectorAll("[data-open-selection]").forEach(function (button) {
    button.addEventListener("click", function () { selectionDialog.showModal(); ensureCatalog(); });
  });
  document.getElementById("selection-copy-md").disabled = true;
  document.getElementById("selection-download-json").disabled = true;
  window.addEventListener("storage", function (event) {
    if (event.key === selectionKey) { selectedIds = loadSelection(); renderSelection(); }
  });
  var globalDialog = document.getElementById("global-search-dialog");
  var globalInput = document.getElementById("global-search-input");
  var globalResults = document.getElementById("global-search-results");
  var globalStatus = document.getElementById("global-search-status");
  function globalSearch() {
    globalResults.textContent = "";
    if (!catalog) { globalStatus.textContent = catalogFailed ? "参考库加载失败，请刷新页面重试。" : "参考库正在加载，请稍后重试。"; return; }
    var q = globalInput.value.trim().toLowerCase();
    var matches = catalog.items.filter(function (item) {
      return !q || [item.name, item.nameZh, item.summary, item.type].concat(item.visualTraits || [], item.styles || [], item.techniques || []).join(" ").toLowerCase().indexOf(q) !== -1;
    });
    globalStatus.textContent = q ? (matches.length ? "找到 " + matches.length + " 个参考" : "没有找到相关参考。试试「按钮」「Linear」或「极简」。") : "";
    matches.slice(0, 30).forEach(function (item) {
      var link = document.createElement("a");
      link.className = "global-search-result";
      link.href = item.url;
      var content = document.createElement("div");
      var title = document.createElement("strong");
      title.textContent = mode() === "en" ? item.name : (item.nameZh + (item.name !== item.nameZh ? " · " + item.name : ""));
      var description = document.createElement("p");
      description.textContent = item.summary || item.name;
      var type = document.createElement("span");
      type.textContent = {"ui-element":"UI 元素", "visual-style":"视觉风格", "site-reference":"知名网站", "logo-reference":"Logo 图鉴", "graphic-reference":"平面设计"}[item.type] || "视觉风格";
      content.append(title, description);
      link.append(content, type);
      globalResults.appendChild(link);
    });
  }
  function openGlobalSearch() {
    if (globalDialog.open) return;
    globalDialog.showModal();
    globalSearch();
    ensureCatalog();
    globalInput.focus();
  }
  document.querySelectorAll("[data-global-search]").forEach(function (button) { button.addEventListener("click", openGlobalSearch); });
  document.getElementById("global-search-close").addEventListener("click", function () { globalDialog.close(); });
  globalDialog.addEventListener("click", function (event) {
    if (event.target !== globalDialog) return;
    var r = globalDialog.getBoundingClientRect();
    if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) globalDialog.close();
  });
  globalInput.addEventListener("input", debounce(globalSearch, 80));
  document.addEventListener("keydown", function (event) {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      if (selectionDialog.open) return;
      if (globalDialog.open) globalDialog.close(); else openGlobalSearch();
    }
  });
  globalDialog.addEventListener("keydown", function (event) {
    if (event.key === "Escape") { event.preventDefault(); globalDialog.close(); return; }
    var results = Array.prototype.slice.call(globalResults.querySelectorAll("a"));
    var index = results.indexOf(document.activeElement);
    if (event.key === "ArrowDown" && results.length) { event.preventDefault(); results[(index + 1) % results.length].focus(); }
    if (event.key === "ArrowUp" && results.length) { event.preventDefault(); if (index <= 0) globalInput.focus(); else results[index - 1].focus(); }
    if (event.key === "Enter" && document.activeElement === globalInput && results.length) { event.preventDefault(); results[0].click(); }
  });
  document.querySelectorAll(".tab[data-filter]").forEach(function (button) {
    button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
    button.addEventListener("click", function () {
      document.querySelectorAll(".tab[data-filter]").forEach(function (tab) { tab.setAttribute("aria-pressed", tab === button ? "true" : "false"); });
    });
  });

  /* ---------- copy buttons ---------- */
  function flash(btn, done) {
    var en = btn.querySelector(".lang-en");
    var zh = btn.querySelector(".lang-zh");
    var oEn = en ? en.textContent : btn.textContent;
    var oZh = zh ? zh.textContent : "";
    btn.classList.add("done");
    if (en) en.textContent = btn.getAttribute("data-done-en") || "Copied";
    if (zh) zh.textContent = btn.getAttribute("data-done-zh") || "已复制";
    if (!en && !zh) btn.textContent = mode() === "en" ? (btn.getAttribute("data-done-en") || "Copied") : (btn.getAttribute("data-done-zh") || "已复制");
    setTimeout(function () {
      btn.classList.remove("done");
      if (en) en.textContent = oEn;
      if (zh) zh.textContent = oZh;
    }, 1600);
  }
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.getAttribute("data-copy"));
      if (!target) return;
      copyText(target.textContent).then(function () { flash(btn); }, function () { btn.textContent = "复制失败，请重试"; });
    });
  });
  var copyMd = document.getElementById("copy-md");
  if (copyMd) {
    copyMd.addEventListener("click", function () {
      var tpl = document.getElementById("md-source");
      if (!tpl) return;
      copyText(tpl.content.textContent).then(function () { flash(copyMd); }, function () { copyMd.textContent = "复制失败，请重试"; });
    });
  }


  /* ---------- double-press a word: plain-English definition ---------- */
  var pop = document.getElementById("def-pop");
  var popWord = document.getElementById("def-word");
  var popBody = document.getElementById("def-body");
  var popSrc = document.getElementById("def-src");
  var hideTimer = null;

  function hidePop() { if (pop) pop.hidden = true; }
  function selectedWord() {
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed) return "";
    var txt = sel.toString().trim();
    var m = txt.match(/[A-Za-z][A-Za-z\-']*/);
    return m ? m[0].toLowerCase() : "";
  }
  document.addEventListener("dblclick", function (ev) {
    if (!pop) return;
    var w = selectedWord();
    if (!w || w.length < 2) { hidePop(); return; }
    popWord.textContent = w;
    popBody.textContent = "Looking up… / 查询中……";
    popSrc.textContent = "plain-English definition";
    pop.hidden = false;
    var x = Math.min(ev.clientX + 12, window.innerWidth - 340);
    var y = Math.min(ev.clientY + 14, window.innerHeight - 160);
    pop.style.left = Math.max(8, x) + "px";
    pop.style.top = Math.max(8, y) + "px";
    clearTimeout(hideTimer);
    fetch("https://api.dictionaryapi.dev/api/v2/entries/en/" + encodeURIComponent(w))
      .then(function (r) { if (!r.ok) throw new Error("nf"); return r.json(); })
      .then(function (data) {
        var meanings = data[0] && data[0].meanings || [];
        var out = [];
        for (var i = 0; i < meanings.length && out.length < 2; i++) {
          var d = meanings[i].definitions && meanings[i].definitions[0];
          if (d) out.push("(" + meanings[i].partOfSpeech + ") " + d.definition);
        }
        popBody.textContent = out.length ? out.join("\n") : "No definition found. / 未找到释义。";
      })
      .catch(function () {
        popBody.textContent = "No definition found. / 未找到释义（网络不可用）。";
      });
    hideTimer = setTimeout(hidePop, 9000);
  });
  document.addEventListener("click", function (ev) {
    if (pop && !pop.hidden && !pop.contains(ev.target)) hidePop();
  });
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") hidePop();
  });

  /* ---------- filter selects: styled dropdown (the native <select> popup cannot be themed) ---------- */
  document.querySelectorAll(".site-filter-select select").forEach(function (sel) {
    var label = sel.closest(".site-filter-select");
    if (!label || label.querySelector(".filter-dropdown")) return;
    var wrap = document.createElement("div");
    wrap.className = "filter-dropdown";
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "filter-dd-button";
    btn.setAttribute("aria-haspopup", "listbox");
    btn.setAttribute("aria-expanded", "false");
    btn.innerHTML = '<span class="filter-dd-label"></span><svg width="10" height="6" viewBox="0 0 10 6" fill="none" aria-hidden="true"><path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    var btnLabel = btn.querySelector(".filter-dd-label");
    var menu = document.createElement("ul");
    menu.className = "filter-dd-menu";
    menu.setAttribute("role", "listbox");
    menu.setAttribute("aria-label", sel.getAttribute("aria-label") || "筛选");
    menu.hidden = true;
    var items = Array.prototype.map.call(sel.options, function (opt, i) {
      var li = document.createElement("li");
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", String(opt.selected));
      if (opt.disabled) li.setAttribute("aria-disabled", "true");
      li.tabIndex = -1;
      li.textContent = opt.textContent;
      li.addEventListener("click", function () { choose(i); });
      menu.appendChild(li);
      return li;
    });
    function sync() {
      btnLabel.textContent = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].textContent : "";
      items.forEach(function (li, i) { li.setAttribute("aria-selected", String(sel.options[i].selected)); });
    }
    function markFocus() { items.forEach(function (li, i) { li.classList.toggle("focus", i === focusIndex); }); }
    var focusIndex = -1;
    function open() {
      wrap.classList.add("open"); menu.hidden = false; btn.setAttribute("aria-expanded", "true");
      focusIndex = sel.selectedIndex; markFocus(); if (items[focusIndex]) items[focusIndex].focus();
    }
    function close() {
      wrap.classList.remove("open"); menu.hidden = true; btn.setAttribute("aria-expanded", "false");
      focusIndex = -1; markFocus(); btn.focus();
    }
    function choose(i) {
      if (sel.options[i].disabled) return;
      if (sel.selectedIndex !== i) { sel.selectedIndex = i; sel.dispatchEvent(new Event("change")); }
      sync(); close();
    }
    function moveFocus(delta) {
      if (!items.length) return;
      focusIndex = (focusIndex + delta + items.length) % items.length;
      markFocus(); items[focusIndex].focus();
    }
    btn.addEventListener("click", function () { wrap.classList.contains("open") ? close() : open(); });
    btn.addEventListener("keydown", function (ev) {
      if (ev.key === "ArrowDown" || ev.key === "ArrowUp" || ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); open(); }
    });
    menu.addEventListener("keydown", function (ev) {
      var i = items.indexOf(ev.target);
      if (i === -1) return;
      if (ev.key === "ArrowDown") { ev.preventDefault(); moveFocus(1); }
      else if (ev.key === "ArrowUp") { ev.preventDefault(); moveFocus(-1); }
      else if (ev.key === "Home") { ev.preventDefault(); focusIndex = -1; moveFocus(1); }
      else if (ev.key === "End") { ev.preventDefault(); focusIndex = 0; moveFocus(-1); }
      else if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); choose(i); }
      else if (ev.key === "Escape" || ev.key === "Tab") { ev.preventDefault(); if (ev.key === "Escape") close(); else { wrap.classList.remove("open"); menu.hidden = true; btn.setAttribute("aria-expanded", "false"); } }
    });
    document.addEventListener("click", function (ev) {
      if (wrap.classList.contains("open") && !wrap.contains(ev.target)) { wrap.classList.remove("open"); menu.hidden = true; btn.setAttribute("aria-expanded", "false"); focusIndex = -1; markFocus(); }
    });
    sel.addEventListener("change", sync);
    wrap.append(btn, menu);
    label.appendChild(wrap);
    sel.classList.add("is-enhanced");
    sync();
  });
})();
