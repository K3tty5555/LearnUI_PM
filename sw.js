/* Cache only requested resources. Never download the whole reference library. */
var VERSION = "__SW_VERSION__";
var CACHE = "learnui-runtime-" + VERSION;
var MAX_ENTRIES = 160;
var OFFLINE = "/offline.html";

self.addEventListener("install", function (event) {
  event.waitUntil(caches.open(CACHE).then(function (cache) {
    return cache.add(OFFLINE).catch(function () {});
  }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener("activate", function (event) {
  event.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (key) {
      return key.indexOf("learnui-") === 0 && key !== CACHE;
    }).map(function (key) { return caches.delete(key); }));
  }).then(function () { return self.clients.claim(); }));
});

async function remember(request, response) {
  if (!response.ok || response.type === "opaque") return;
  var cache = await caches.open(CACHE);
  var key = request;
  if (request.mode === "navigate") { var url = new URL(request.url); url.search = ""; key = url.href; }
  await cache.put(key, response.clone());
  var keys = await cache.keys();
  var removable = keys.filter(function (key) { return new URL(key.url).pathname !== OFFLINE; });
  await Promise.all(removable.slice(0, Math.max(0, keys.length - MAX_ENTRIES)).map(function (key) { return cache.delete(key); }));
}

self.addEventListener("fetch", function (event) {
  var request = event.request;
  var url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;
  if (url.pathname.endsWith("/sw.js")) return;
  var navigation = request.mode === "navigate";
  var scope = new URL(self.registration.scope).pathname;
  var resource = url.pathname.indexOf(scope + "assets/") === 0 || url.pathname.indexOf(scope + "api/") === 0;
  if (!navigation && !resource) return;

  // Lifetime is registered synchronously, before any cache lookup yields.
  var release;
  event.waitUntil(new Promise(function (resolve) { release = resolve; }));
  event.respondWith((async function () {
    var cache = await caches.open(CACHE);
    var hit = await cache.match(request, { ignoreSearch: navigation });
    // Versioned static assets are immutable during this worker's lifetime.
    if (hit && !navigation) { release(); return hit; }
    var network = fetch(request).then(async function (response) {
      try { await remember(request, response); } catch (error) { /* Cache quota must not break a successful load. */ }
      return response;
    });
    network.then(release, release);
    if (hit) return hit; // Immediate repeat navigation; update in the background.
    try { return await network; }
    catch (error) {
      if (navigation) {
        return await cache.match(OFFLINE) || new Response("Offline. Reconnect and reload.", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
      }
      return Response.error();
    }
  })().catch(function () { release(); return fetch(request); }));
});
