/* Learn UI PM site chrome JS */
(function () {
  "use strict";

  /* ---------- service worker (PWA) ---------- */
  var isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
  if ("serviceWorker" in navigator && (location.protocol === "https:" || isLocal)) {
    window.addEventListener("load", function () {
      // The offline library is large. Warm it after the visible page has settled
      // so precaching never competes with the first useful screen.
      window.setTimeout(function () {
        navigator.serviceWorker.register("/sw.js").catch(function () {});
      }, 8000);
    });
  }

  /* ---------- language mode ---------- */
  var MODE_KEY = "ntui-lang-mode";
  // 首次访问（无本地偏好）按浏览器语言决定：中文环境 → 纯中文，其他 → 纯英文。
  // 与 <head> 内联探测脚本保持一致；用户手动切换后才写 localStorage。
  function detectMode() {
    return "zh";
  }
  function mode() {
    try { return localStorage.getItem(MODE_KEY) || detectMode(); } catch (e) { return detectMode(); }
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
    var walker = document.createTreeWalker(fragment, NodeFilter.SHOW_TEXT);
    var node;
    translatingDemos = true;
    while ((node = walker.nextNode())) translateDemoText(node, slug, toChinese);
    fragment.querySelectorAll("[placeholder],[title],[aria-label],[value]").forEach(function (el) {
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
    var input = document.getElementById("search") || document.getElementById("style-search") || document.getElementById("site-search");
    if (input) {
      var ph = m === "en" ? input.getAttribute("data-ph-en")
        : m === "zh" ? input.getAttribute("data-ph-zh")
        : input.getAttribute("data-ph-zh") + " / " + input.getAttribute("data-ph-en");
      input.setAttribute("placeholder", ph);
    }
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

  document.querySelectorAll(".site-nav a").forEach(function (link) {
    var href = link.getAttribute("href") || "";
    var path = location.pathname;
    var current = (href === "/#dictionary" && path === "/")
      || (href === "/references/" && path.indexOf("/references/") === 0)
      || (href === "/sites/" && path.indexOf("/sites/") === 0)
      || (href === "/styles/" && path.indexOf("/styles/") === 0)
      || (href === "/#guides" && path.indexOf("/guides/") === 0 && path !== "/guides/translate/")
      || (href === "/guides/translate/" && path === "/guides/translate/");
    link.classList.toggle("current", current);
    if (current) link.setAttribute("aria-current", "page");
  });

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
    if ((ev.key === "/" && !typing) || ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === "k")) {
      var inp = document.getElementById("search") || document.getElementById("style-search") || document.getElementById("site-search") || document.getElementById("reference-search") || document.getElementById("table-search");
      if (inp) { ev.preventDefault(); inp.focus(); inp.select(); }
    }
    if (ev.key === "Escape" && typing) {
      var active = document.activeElement;
      if (active && (active.id === "search" || active.id === "style-search" || active.id === "site-search" || active.id === "reference-search" || active.id === "table-search")) {
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
    var INDEX = JSON.parse(indexEl.textContent);
    var bySlug = {};
    INDEX.forEach(function (it) { bySlug[it.slug] = it; });
    var cards = Array.prototype.slice.call(document.querySelectorAll(".catalog-item[data-platform]"));
    var searchInput = document.getElementById("search");
    var noResult = document.getElementById("no-result");
    var countNote = document.getElementById("count-note");
    var tabBtns = Array.prototype.slice.call(document.querySelectorAll(".tab[data-filter]"));
    var state = { q: "", platform: "all" };

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
    if (qp || qq) apply();

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

  /* ---------- famous sites: search and category ---------- */
  var siteInput = document.getElementById("site-search");
  if (siteInput) {
    var siteCards = Array.prototype.slice.call(document.querySelectorAll(".sites-card"));
    var siteNoResult = document.getElementById("site-no-result");
    var siteCount = document.getElementById("site-count");
    var siteTabs = Array.prototype.slice.call(document.querySelectorAll(".cat-tab"));
    var siteParams = new URLSearchParams(location.search);
    var siteCategory = siteParams.get("category") || "";
    if (!siteTabs.some(function (tab) { return tab.getAttribute("data-cat") === siteCategory; })) siteCategory = "";

    var applySites = function () {
      var query = siteInput.value.trim().toLowerCase();
      var visible = 0;
      siteCards.forEach(function (card) {
        var matches = (!siteCategory || card.getAttribute("data-cat") === siteCategory)
          && (!query || (card.getAttribute("data-search") || "").indexOf(query) !== -1);
        card.hidden = !matches;
        if (matches) visible++;
      });
      if (siteNoResult) siteNoResult.hidden = visible !== 0;
      if (siteCount) {
        siteCount.querySelectorAll("[data-tpl]").forEach(function (el) {
          el.textContent = el.getAttribute("data-tpl").replace("{n}", (query || siteCategory) ? visible + " / " + siteCards.length : visible);
        });
      }
    };
    var applySitesD = debounce(applySites, 80);
    var syncSitesD = debounce(function () {
      syncURL({ q: siteInput.value.trim() || null, category: siteCategory || null });
    }, 200);
    siteInput.addEventListener("input", function () { applySitesD(); syncSitesD(); });
    siteTabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        siteCategory = tab.getAttribute("data-cat") || "";
        siteTabs.forEach(function (item) {
          var selected = item === tab;
          item.classList.toggle("active", selected);
          item.setAttribute("aria-pressed", selected ? "true" : "false");
        });
        tab.scrollIntoView({ block: "nearest", inline: "nearest" });
        applySites();
        syncURL({ q: siteInput.value.trim() || null, category: siteCategory || null });
      });
    });
    siteInput.value = siteParams.get("q") || "";
    siteTabs.forEach(function (tab) {
      var selected = tab.getAttribute("data-cat") === siteCategory;
      tab.classList.toggle("active", selected);
      tab.setAttribute("aria-pressed", selected ? "true" : "false");
    });
    applySites();
  }

  /* ---------- page-reference filters ---------- */
  var referenceIndexEl = document.getElementById("reference-index");
  if (referenceIndexEl) {
    var refIndex = JSON.parse(referenceIndexEl.textContent);
    var refBySlug = {};
    refIndex.forEach(function (item) { refBySlug[item.slug] = item; });
    var refCards = Array.prototype.slice.call(document.querySelectorAll(".reference-card-item"));
    var refInput = document.getElementById("reference-search");
    var refChecks = Array.prototype.slice.call(document.querySelectorAll("[data-ref-filter]"));
    var refDetails = Array.prototype.slice.call(document.querySelectorAll(".reference-filter-group"));
    var refCount = document.getElementById("reference-count");
    var refEmpty = document.getElementById("reference-no-result");
    var refReset = document.getElementById("reference-reset");
    var refGroups = ["productTypes", "pageTypes", "layouts", "moods", "states"];

    if (window.matchMedia("(max-width: 760px)").matches) {
      refDetails.forEach(function (details) {
        details.open = false;
        details.addEventListener("toggle", function () {
          if (!details.open) return;
          refDetails.forEach(function (other) { if (other !== details) other.open = false; });
        });
      });
    }

    function selectedFor(group) {
      return refChecks.filter(function (box) {
        return box.checked && box.getAttribute("data-ref-filter") === group;
      }).map(function (box) { return box.value; });
    }

    function refApply() {
      var query = refInput.value.trim().toLowerCase();
      var visible = 0;
      refCards.forEach(function (card) {
        var item = refBySlug[card.getAttribute("data-reference-slug")];
        var hay = [item.title, item.titleEn, item.summary]
          .concat(item.scenarios || [], item.structure || [], item.visualTraits || []).join(" ").toLowerCase();
        var ok = !query || hay.indexOf(query) !== -1;
        refGroups.forEach(function (group) {
          var selected = selectedFor(group);
          if (selected.length && !selected.some(function (value) { return (item[group] || []).indexOf(value) !== -1; })) ok = false;
        });
        card.hidden = !ok;
        if (ok) visible++;
      });
      refCount.textContent = visible + " / " + refCards.length + " 个参考";
      refEmpty.hidden = visible !== 0;
    }

    function refSync() {
      var params = { q: refInput.value.trim() || null };
      refGroups.forEach(function (group) {
        var values = selectedFor(group);
        params[group] = values.length ? values.join(",") : null;
      });
      syncURL(params);
    }

    var refApplyD = debounce(refApply, 60);
    var refSyncD = debounce(refSync, 180);
    refInput.addEventListener("input", function () { refApplyD(); refSyncD(); });
    refChecks.forEach(function (box) {
      box.addEventListener("change", function () { refApply(); refSyncD(); });
    });
    refReset.addEventListener("click", function () {
      refInput.value = "";
      refChecks.forEach(function (box) { box.checked = false; });
      refApply();
      refSync();
    });

    var refParams = new URLSearchParams(location.search);
    refInput.value = refParams.get("q") || "";
    refGroups.forEach(function (group) {
      var values = (refParams.get(group) || "").split(",").filter(Boolean);
      refChecks.forEach(function (box) {
        if (box.getAttribute("data-ref-filter") === group) box.checked = values.indexOf(box.value) !== -1;
      });
    });
    refApply();
  }

  /* ---------- reference specimen states ---------- */
  document.querySelectorAll("[data-pm-demo] [data-demo-state]").forEach(function (button) {
    button.addEventListener("click", function () {
      var demo = button.closest("[data-pm-demo]");
      var state = button.getAttribute("data-demo-state");
      demo.querySelectorAll("[data-demo-state]").forEach(function (item) {
        item.classList.toggle("active", item === button);
      });
      demo.querySelectorAll("[data-demo-panel]").forEach(function (panel) {
        panel.hidden = panel.getAttribute("data-demo-panel") !== state;
      });
    });
  });

  /* ---------- cross-catalog selection and export ---------- */
  var selectionKey = "learnui-selection-v1";
  var selectionDialog = document.getElementById("selection-dialog");
  var selectionDock = document.getElementById("selection-dock");
  var selectionCount = document.getElementById("selection-count");
  var selectionList = document.getElementById("selection-list");
  var selectionEmpty = document.getElementById("selection-empty");
  var selectionStatus = document.getElementById("selection-status");
  var catalog = null;
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
      var label = button.querySelector("[data-select-label]");
      if (label) label.textContent = active ? "已加入" : "加入参考";
    });
  }

  function renderSelection() {
    if (!selectionList) return;
    var items = selectedItems();
    selectionList.textContent = "";
    items.forEach(function (item) {
      var row = document.createElement("div");
      row.className = "selection-row";
      var link = document.createElement("a");
      link.href = item.url;
      link.textContent = item.nameZh + (item.name ? " / " + item.name : "");
      var type = document.createElement("span");
      type.textContent = item.type === "page-reference" ? "页面参考" : item.type === "ui-element" ? "UI 元素" : "视觉风格";
      var remove = document.createElement("button");
      remove.type = "button";
      remove.className = "icon-button";
      remove.setAttribute("aria-label", "移除 " + item.nameZh);
      remove.textContent = "×";
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
    refreshSelectionButtons();
  }

  function exportPayload() {
    var items = selectedItems();
    return {
      schemaVersion: 1,
      language: "zh-CN",
      purpose: "用于 AI 原型生成的 UI 参考说明",
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
    selectedItems().forEach(function (item) {
      lines.push("## " + item.nameZh + (item.name ? " (" + item.name + ")" : ""), "");
      lines.push("- 类型：" + (item.type === "page-reference" ? "页面参考" : item.type === "ui-element" ? "UI 元素" : "视觉风格"));
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
      renderSelection();
    });
  });

  if (selectionDialog) {
    document.getElementById("selection-open").addEventListener("click", function () {
      if (selectionDialog.showModal) selectionDialog.showModal();
      else selectionDialog.setAttribute("open", "");
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
      navigator.clipboard.writeText(exportMarkdown()).then(function () { setSelectionStatus("Markdown 已复制"); });
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

  fetch("/api/catalog.json").then(function (response) {
    if (!response.ok) throw new Error("catalog unavailable");
    return response.json();
  }).then(function (data) {
    catalog = data;
    data.items.forEach(function (item) { catalogById[item.id] = item; });
    selectedIds = selectedIds.filter(function (id) { return Boolean(catalogById[id]); });
    saveSelection();
    renderSelection();
  }).catch(function () {
    refreshSelectionButtons();
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
    if (!en && !zh) btn.textContent = btn.getAttribute("data-done-en") || "Copied";
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
      navigator.clipboard.writeText(target.textContent).then(function () { flash(btn); }, function () {});
    });
  });
  var copyMd = document.getElementById("copy-md");
  if (copyMd) {
    copyMd.addEventListener("click", function () {
      var tpl = document.getElementById("md-source");
      if (!tpl) return;
      navigator.clipboard.writeText(tpl.innerHTML).then(function () { flash(copyMd); }, function () {});
    });
  }

  /* ---------- translate table filter ---------- */
  var tableInput = document.getElementById("table-search");
  if (tableInput) {
    var rows = Array.prototype.slice.call(document.querySelectorAll("#translate-table tbody tr"));
    var cnt = document.getElementById("table-count");
    var cntZh = document.getElementById("table-count-zh");
    tableInput.addEventListener("input", debounce(function () {
      var q = tableInput.value.trim().toLowerCase();
      var n = 0;
      rows.forEach(function (r) {
        var ok = !q || r.getAttribute("data-search").indexOf(q) !== -1;
        r.style.display = ok ? "" : "none";
        if (ok) n++;
      });
      if (cnt) cnt.textContent = cnt.getAttribute("data-tpl").replace("{n}", n).replace("{total}", rows.length);
      if (cntZh) cntZh.textContent = cntZh.getAttribute("data-tpl").replace("{n}", n).replace("{total}", rows.length);
    }, 80));
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
})();
