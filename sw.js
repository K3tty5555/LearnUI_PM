/* Learn UI PM service worker. Version stamped by build.py. */
var VERSION = "__SW_VERSION__";
var ASSET_VERSION = "__ASSET_VERSION__";
var SHELL = "learnui-shell-" + VERSION;
var PAGES = "learnui-pages-" + VERSION;
var GENERATED_PAGES = __PRECACHE_PAGES__;
function revision(path) { return path + "?v=" + ASSET_VERSION; }

var PRECACHE = Array.from(new Set([
  "/",
  "/styles/",
  "/references/",
  "/manifest.webmanifest",
  revision("/assets/site.css"),
  revision("/assets/reference-demos.css"),
  revision("/assets/glass-theme.css"),
  revision("/assets/demo-i18n.js"),
  revision("/assets/site.js"),
  "/assets/og/style-frutiger-aero.png",
  "/api/catalog.json",
  "/api/demo-i18n.json",
  "/api/taxonomy.json",
  "/assets/fonts/geist-vf.woff2",
  "/assets/fonts/geist-mono-vf.woff2",
  "/assets/icons/favicon-32.png",
  "/assets/icons/ai-pm-client-circle-64.png",
  "/assets/icons/icon-192.png",
  "/assets/icons/icon-512.png",
  "/assets/icons/apple-touch-icon.png"
].concat(GENERATED_PAGES)));

self.addEventListener("install", function (ev) {
  ev.waitUntil(
    caches.open(SHELL).then(function (c) { return c.addAll(PRECACHE); }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener("activate", function (ev) {
  ev.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k !== SHELL && k !== PAGES) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (ev) {
  var req = ev.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin !== location.origin) return;
  var scopePath = new URL(self.registration.scope).pathname.replace(/\/$/, "");
  var assetsPath = scopePath + "/assets/";

  // Static assets: cache-first, then network (and fill cache).
  if (url.pathname.indexOf(assetsPath) === 0 || url.pathname === scopePath + "/manifest.webmanifest") {
    ev.respondWith(
      caches.match(req).then(function (hit) {
        return hit || fetch(req).then(function (res) {
          if (res.ok) {
            var copy = res.clone();
            caches.open(SHELL).then(function (c) { c.put(req, copy); });
          }
          return res;
        });
      })
    );
    return;
  }

  // Pages: network-first, fall back to cache, then to cached home.
  if (req.mode === "navigate" || (req.headers.get("accept") || "").indexOf("text/html") !== -1) {
    ev.respondWith(
      fetch(req).then(function (res) {
        if (res.ok) {
          var copy = res.clone();
          caches.open(PAGES).then(function (c) { c.put(req, copy); });
        }
        return res;
      }).catch(function () {
        return caches.match(req).then(function (hit) {
          return hit || caches.match("/");
        });
      })
    );
  }
});
