/* Backlog Boss design prototypes — shared interaction layer.
   Plain vanilla JavaScript, no frameworks, no build step.
   Implements: catalog search + genre filtering, sorting (score / time /
   blended), add-to-backlog, complete with undo, remove with confirm,
   refresh simulation, home stats, and the logged-out sign-in preview. */

(function () {
  "use strict";

  var CATALOG = window.BB_GAMES || [];
  var SITE = document.body.dataset.site || "proto";
  var PAGE = document.body.dataset.page || "home";

  var STORE_KEY = "bb-proto." + SITE;
  var QUERY_KEY = STORE_KEY + ".query";

  /* ------------------------------ model ------------------------------ */

  var SEED = [
    { gameId: 1145360, addedOn: "2026-07-12" },
    { gameId: 367520, addedOn: "2026-07-02" },
    { gameId: 1245620, addedOn: "2026-06-28" },
    { gameId: 632470, addedOn: "2026-06-20" },
    { gameId: 870780, addedOn: "2026-06-11" },
    { gameId: 427520, addedOn: "2026-06-05" },
    { gameId: 1238810, addedOn: "2026-05-27" },
    { gameId: 858820, addedOn: "2026-05-19" },
    { gameId: 1593500, addedOn: "2026-05-10" },
    { gameId: 960090, addedOn: "2026-05-02" },
    { gameId: 782330, addedOn: "2026-04-22" },
    { gameId: 1086940, addedOn: "2026-04-15" },
    { gameId: 620, addedOn: "2026-03-01", completedOn: "2026-03-18" },
    { gameId: 504230, addedOn: "2026-02-20", completedOn: "2026-03-02" },
    { gameId: 413150, addedOn: "2026-01-30", completedOn: "2026-02-14" }
  ];

  function loadEntries() {
    var raw = null;
    try {
      raw = localStorage.getItem(STORE_KEY);
    } catch (e) {
      /* storage unavailable — run in-memory only */
    }
    if (raw) {
      try {
        return JSON.parse(raw);
      } catch (e) {
        /* corrupted state — reseed below */
      }
    }
    return reseed();
  }

  function reseed() {
    var entries = SEED.map(function (s) {
      return { gameId: s.gameId, addedOn: s.addedOn, completedOn: s.completedOn || null };
    });
    saveEntries(entries);
    return entries;
  }

  function saveEntries(entries) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(entries));
    } catch (e) {
      /* ignore — prototype degrades gracefully */
    }
  }

  var entries = loadEntries();

  function gameById(id) {
    for (var i = 0; i < CATALOG.length; i++) {
      if (CATALOG[i].id === id) return CATALOG[i];
    }
    return null;
  }

  function entryByGameId(id) {
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].gameId === id) return entries[i];
    }
    return null;
  }

  function inBacklog(id) {
    return !!entryByGameId(id);
  }

  /* --------------------------- tiny helpers --------------------------- */

  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function $$(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        if (key === "class") node.className = attrs[key];
        else if (key === "text") node.textContent = attrs[key];
        else node.setAttribute(key, attrs[key]);
      });
    }
    (children || []).forEach(function (child) {
      if (typeof child === "string") node.appendChild(document.createTextNode(child));
      else if (child) node.appendChild(child);
    });
    return node;
  }

  function fmtHours(hours) {
    return Math.round(hours) + " h";
  }

  function fmtDate(iso) {
    if (!iso) return "";
    return new Date(iso + "T12:00:00").toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  }

  function platformLabel(platforms) {
    if (!platforms || !platforms.length) return "PC";
    return platforms.join(" · ");
  }

  function todayIso() {
    return new Date().toISOString().slice(0, 10);
  }

  /* --------------------- sorting (mirrors the app) --------------------- */

  function blendedComparator(list, a, b) {
    var scores = list.map(function (e) { return e.game.rating || 0; });
    var times = list
      .map(function (e) { return e.game.hours; })
      .filter(function (h) { return h != null; });

    var minScore = Math.min.apply(null, scores);
    var maxScore = Math.max.apply(null, scores);
    var hasTimes = times.length > 0;
    var minTime = hasTimes ? Math.min.apply(null, times) : 0;
    var maxTime = hasTimes ? Math.max.apply(null, times) : 0;

    var scoreRange = maxScore - minScore || 1;
    var timeRange = maxTime - minTime || 1;

    var normalizeScore = function (score) {
      return score ? (score - minScore) / scoreRange : -1;
    };
    var normalizeTime = function (hours) {
      return hours != null ? (maxTime - hours) / timeRange : -1;
    };

    var timeWeight = 3;
    var scoreA = normalizeScore(a.game.rating) + normalizeTime(a.game.hours) * timeWeight;
    var scoreB = normalizeScore(b.game.rating) + normalizeTime(b.game.hours) * timeWeight;
    return scoreB - scoreA;
  }

  function sortDecorated(decorated, sortType) {
    if (sortType === "score") {
      return decorated.sort(function (a, b) {
        return (b.game.rating || 0) - (a.game.rating || 0);
      });
    }
    if (sortType === "time") {
      return decorated.sort(function (a, b) {
        return (a.game.hours == null ? Infinity : a.game.hours) -
          (b.game.hours == null ? Infinity : b.game.hours);
      });
    }
    return decorated.sort(function (a, b) {
      return blendedComparator(decorated, a, b);
    });
  }

  function decorate(entriesToDecorate) {
    return entriesToDecorate.map(function (entry) {
      return { entry: entry, game: gameById(entry.gameId) };
    }).filter(function (d) { return d.game; });
  }

  /* ------------------------------- toasts ------------------------------ */

  var toastStack = null;

  function ensureToastStack() {
    if (!toastStack) {
      toastStack = el("div", { class: "toast-stack", "aria-live": "polite" });
      document.body.appendChild(toastStack);
    }
    return toastStack;
  }

  function toast(message, actionLabel, onAction, duration) {
    var stack = ensureToastStack();
    var close = function () {
      item.classList.add("toast--leaving");
      setTimeout(function () { item.remove(); }, 220);
    };
    var item = el("div", { class: "toast" });
    var body = el("span", { class: "toast__message", text: message });
    item.appendChild(body);
    if (actionLabel && onAction) {
      var button = el("button", { class: "toast__action", text: actionLabel });
      button.addEventListener("click", function () {
        onAction();
        close();
      });
      item.appendChild(button);
    }
    item.appendChild(el("button", { class: "toast__dismiss", "aria-label": "Dismiss", text: "×" }));
    item.querySelector(".toast__dismiss").addEventListener("click", close);
    stack.appendChild(item);
    setTimeout(close, duration || 5000);
    return item;
  }

  /* --------------------------- confirm modal --------------------------- */

  function confirmModal(title, bodyText, confirmLabel) {
    return new Promise(function (resolve) {
      var overlay = el("div", { class: "modal-overlay" });
      var modal = el("div", { class: "modal", role: "dialog", "aria-modal": "true" });
      modal.appendChild(el("h3", { class: "modal__title", text: title }));
      modal.appendChild(el("p", { class: "modal__body", text: bodyText }));
      var actions = el("div", { class: "modal__actions" });
      var cancel = el("button", { class: "btn btn--secondary", text: "Cancel" });
      var confirm = el("button", { class: "btn btn--danger", text: confirmLabel });
      cancel.addEventListener("click", function () { overlay.remove(); resolve(false); });
      confirm.addEventListener("click", function () { overlay.remove(); resolve(true); });
      actions.appendChild(cancel);
      actions.appendChild(confirm);
      modal.appendChild(actions);
      overlay.appendChild(modal);
      document.body.appendChild(overlay);
      confirm.focus();
    });
  }

  /* ---------------------- shared row rendering -------------------------
     One generic row structure for the backlog list, the search results
     and the home "top picks". Each site's stylesheet re-skins it. */

  function rowFragment(game, extra) {
    extra = extra || {};
    var frag = document.createDocumentFragment();

    if (extra.index) {
      frag.appendChild(el("span", { class: "game-row__index", text: String(extra.index) }));
    }

    var cover = extra.coverAlt
      ? el("div", { class: "cover cover--thumb is-fallback", "aria-hidden": "true" })
      : el("img", { class: "cover cover--thumb", src: game.cover, alt: game.title + " cover", loading: "lazy" });

    var title = el("h3", { class: "game-row__title", text: game.title });
    var info = el("div", { class: "game-row__info" });
    info.appendChild(title);
    if (extra.subtitle) {
      info.appendChild(el("p", { class: "game-row__subtitle", text: extra.subtitle }));
    }

    var meta = el("div", { class: "game-row__meta" });
    meta.appendChild(el("span", { class: "game-row__rating", text: game.rating + "/100" }));
    meta.appendChild(el("span", { class: "game-row__sep", text: "·" }));
    meta.appendChild(el("span", { class: "game-row__hours", text: fmtHours(game.hours) + " to beat" }));

    var genres = el("div", { class: "game-row__genres" });
    game.genres.forEach(function (genre) {
      genres.appendChild(el("span", { class: "game-row__genre", text: genre }));
    });

    var body = el("div", { class: "game-row__body" });
    body.appendChild(info);
    body.appendChild(meta);
    body.appendChild(genres);

    var row = el("div", { class: "game-row", "data-game": String(game.id) });
    row.appendChild(cover);
    row.appendChild(body);

    if (extra.side) {
      row.appendChild(extra.side);
    }

    frag.appendChild(row);
    return frag;
  }

  /* ============================== HOME ================================= */

  function renderHomeStats() {
    var active = entries.filter(function (e) { return !e.completedOn; });
    var completed = entries.filter(function (e) { return e.completedOn; });

    var fill = $(`[data-stat="active"]`);
    if (fill) fill.textContent = String(active.length);

    fill = $(`[data-stat="completed"]`);
    if (fill) fill.textContent = String(completed.length);

    fill = $(`[data-stat="hours"]`);
    if (fill) {
      var hours = active.reduce(function (sum, e) {
        var game = gameById(e.gameId);
        return sum + (game ? game.hours : 0);
      }, 0);
      fill.textContent = fmtHours(hours);
    }

    fill = $(`[data-stat="score"]`);
    if (fill) {
      var rated = active.map(function (e) { return gameById(e.gameId); }).filter(Boolean);
      var avg = rated.length
        ? Math.round(rated.reduce(function (sum, g) { return sum + g.rating; }, 0) / rated.length)
        : 0;
      fill.textContent = avg + "/100";
    }
  }

  function renderTopPicks() {
    var mount = $("[data-picks]");
    if (!mount) return;
    if (mount.dataset.rendered) return;

    var active = entries.filter(function (e) { return !e.completedOn; });
    var picks = sortDecorated(decorate(active), "blended").slice(0, 3);

    picks.forEach(function (pick, i) {
      var side = el("div", { class: "game-row__side" });
      var add = el("button", {
        class: "btn btn--small",
        text: "Complete",
        "aria-label": "Complete " + pick.game.title
      });
      add.addEventListener("click", function () { toggleComplete(pick.entry); });
      side.appendChild(add);
      mount.appendChild(rowFragment(pick.game, {
        index: i + 1,
        subtitle: "Next up · blended score",
        side: side
      }));
    });

    mount.dataset.rendered = "1";
  }

  /* ------------------------- sign-in preview --------------------------- */

  function renderSigninPreview() {
    var toggle = $("[data-toggle-signin]");
    if (!toggle) return;

    var previewing = document.body.classList.contains("signin-preview");

    var update = function () {
      var isPreviewing = document.body.classList.contains("signin-preview");
      toggle.textContent = isPreviewing
        ? "Back to signed-in view"
        : "Preview what new visitors see";
    };

    toggle.addEventListener("click", function () {
      document.body.classList.toggle("signin-preview");
      update();
    });
    update();
  }

  /* ============================ SEARCH PAGE ============================ */

  var currentApplyFilters = null;

  function buildGenreChips(mount) {
    var genres = {};
    CATALOG.forEach(function (game) {
      game.genres.forEach(function (genre) { genres[genre] = true; });
    });
    var names = Object.keys(genres).sort();
    var active = {};

    function applyFilters() {
      var query = $("[data-search]").value.trim().toLowerCase();
      var results = CATALOG.filter(function (game) {
        if (query && game.title.toLowerCase().indexOf(query) === -1) return false;
        for (var i = 0; i < game.genres.length; i++) {
          if (active[game.genres[i]]) return true;
        }
        return !Object.keys(active).length;
      });
      results.sort(function (a, b) { return (b.rating || 0) - (a.rating || 0); });
      renderResults(results, query);
    }

    names.forEach(function (name) {
      var chip = el("button", {
        class: "genre-chip",
        type: "button",
        "aria-pressed": "false",
        text: name
      });
      chip.addEventListener("click", function () {
        var isActive = !active[name];
        active[name] = isActive;
        chip.classList.toggle("is-active", isActive);
        chip.setAttribute("aria-pressed", String(isActive));
        applyFilters();
      });
      mount.appendChild(chip);
    });

    return applyFilters;
  }

  function buildSearch() {
    var input = $("[data-search]");
    var mount = $("[data-genres]");
    var restored = "";
    try {
      restored = localStorage.getItem(QUERY_KEY) || "";
    } catch (e) { /* ignore */ }
    input.value = restored;

    var applyFilters = buildGenreChips(mount);
    currentApplyFilters = applyFilters;

    input.addEventListener("input", function () {
      try {
        localStorage.setItem(QUERY_KEY, input.value);
      } catch (e) { /* ignore */ }
      applyFilters();
    });

    applyFilters();
  }

  function renderResults(results, query) {
    var mount = $("[data-results]");
    var count = $("[data-count]");
    var hint = $("[data-hint]");

    mount.innerHTML = "";

    if (count) {
      count.textContent = query
        ? results.length + " game" + (results.length === 1 ? "" : "s") + " for \u201c" + query + "\u201d"
        : results.length + " games in the catalog";
    }

    if (hint) hint.classList.toggle("is-hidden", !!query || results.length > 0);
    if (!query && !results.length) return;

    results.forEach(function (game) {
      var side = el("div", { class: "game-row__side" });
      if (inBacklog(game.id)) {
        side.appendChild(el("span", { class: "chip chip--in-backlog", text: "In backlog" }));
      } else {
        var add = el("button", {
          class: "btn btn--small btn--primary",
          text: "Add to backlog",
          "aria-label": "Add " + game.title + " to backlog"
        });
        add.addEventListener("click", function () { addToBacklog(game); });
        side.appendChild(add);
      }
      mount.appendChild(rowFragment(game, { side: side }));
    });

    if (!results.length) {
      mount.appendChild(el("div", {
        class: "empty",
        text: "No games match \u201c" + query + "\u201d. Try another title."
      }));
    }
  }

  function addToBacklog(game) {
    if (inBacklog(game.id)) return;
    entries.push({ gameId: game.id, addedOn: todayIso(), completedOn: null });
    saveEntries(entries);
    if (currentApplyFilters) currentApplyFilters();
    toast("\u201c" + game.title + "\u201d was added to your backlog", "View backlog", function () {
      window.location.href = "backlog.html";
    });
  }

  /* ============================ BACKLOG PAGE ============================ */

  function toggleComplete(entry) {
    var wasCompleted = !!entry.completedOn;
    var previous = entry.completedOn;
    entry.completedOn = wasCompleted ? null : todayIso();
    saveEntries(entries);
    renderBacklog();

    if (!wasCompleted) {
      toast("\u201c" + gameById(entry.gameId).title + "\u201d marked as complete", "Undo", function () {
        var current = entryByGameId(entry.gameId);
        if (current) {
          current.completedOn = previous;
          saveEntries(entries);
          renderBacklog();
        }
      });
    }
  }

  function renderBacklog() {
    var activeMount = $('[data-bblist="active"]');
    var completedMount = $('[data-bblist="completed"]');
    var empty = $("[data-empty]");

    var sortType = "score";
    try {
      sortType = localStorage.getItem(STORE_KEY + ".sort") || "score";
    } catch (e) { /* ignore */ }

    var decorated = decorate(entries);
    var active = decorated.filter(function (d) { return !d.entry.completedOn; });
    var completed = decorated.filter(function (d) { return d.entry.completedOn; });

    sortDecorated(active, sortType);
    sortDecorated(completed, sortType);

    var activeCount = $("[data-count-active]");
    var completedCount = $("[data-count-completed]");
    if (activeCount) activeCount.textContent = String(active.length);
    if (completedCount) completedCount.textContent = String(completed.length);

    if (empty) empty.classList.toggle("is-hidden", active.length > 0);
    if (activeMount) activeMount.innerHTML = "";
    if (completedMount) completedMount.innerHTML = "";

    active.forEach(function (d) {
      var entry = d.entry;
      var side = el("div", { class: "game-row__side" });
      var completeBtn = el("button", {
        class: "btn btn--small",
        text: "Mark complete",
        "aria-label": "Mark " + d.game.title + " as complete"
      });
      completeBtn.addEventListener("click", function () { toggleComplete(entry); });
      side.appendChild(completeBtn);

      var removeBtn = el("button", {
        class: "btn btn--small btn--ghost",
        text: "Remove",
        "aria-label": "Remove " + d.game.title + " from backlog"
      });
      removeBtn.addEventListener("click", function () {
        confirmModal(
          "Remove from backlog?",
          "\u201c" + d.game.title + "\u201d will leave your backlog. This removes your progress for this game.",
          "Remove"
        ).then(function (confirmed) {
          if (!confirmed) return;
          entries = entries.filter(function (e) { return e.gameId !== d.game.id; });
          saveEntries(entries);
          renderBacklog();
          toast("\u201c" + d.game.title + "\u201d was removed from your backlog");
        });
      });
      side.appendChild(removeBtn);

      var addedOn = "Added " + fmtDate(entry.addedOn);
      activeMount.appendChild(rowFragment(d.game, { subtitle: addedOn, side: side }));
    });

    completed.forEach(function (d) {
      var entry = d.entry;
      var side = el("div", { class: "game-row__side" });
      var undoCompleteBtn = el("button", {
        class: "btn btn--small btn--ghost",
        text: "Reopen",
        "aria-label": "Reopen " + d.game.title
      });
      undoCompleteBtn.addEventListener("click", function () { toggleComplete(entry); });
      side.appendChild(undoCompleteBtn);

      var removeBtn = el("button", {
        class: "btn btn--small btn--ghost",
        text: "Remove",
        "aria-label": "Remove " + d.game.title + " from backlog"
      });
      removeBtn.addEventListener("click", function () {
        confirmModal(
          "Remove from backlog?",
          "\u201c" + d.game.title + "\u201d will leave your backlog, including its completion history.",
          "Remove"
        ).then(function (confirmed) {
          if (!confirmed) return;
          entries = entries.filter(function (e) { return e.gameId !== d.game.id; });
          saveEntries(entries);
          renderBacklog();
          toast("\u201c" + d.game.title + "\u201d was removed from your backlog");
        });
      });
      side.appendChild(removeBtn);

      var completedOn = "Completed " + fmtDate(entry.completedOn);
      completedMount.appendChild(rowFragment(d.game, { subtitle: completedOn, side: side }));
    });
  }

  function buildSortControls() {
    var controls = $$("[data-sort]");
    if (!controls.length) return;

    var activeSort = "score";
    try {
      activeSort = localStorage.getItem(STORE_KEY + ".sort") || "score";
    } catch (e) { /* ignore */ }

    function setSort(type) {
      activeSort = type;
      try {
        localStorage.setItem(STORE_KEY + ".sort", type);
      } catch (e) { /* ignore */ }
      controls.forEach(function (control) {
        var isActive = control.dataset.sort === type;
        control.classList.toggle("is-active", isActive);
        control.setAttribute("aria-pressed", String(isActive));
      });
    }

    controls.forEach(function (control) {
      control.addEventListener("click", function () {
        setSort(control.dataset.sort);
        renderBacklog();
      });
    });

    setSort(activeSort);
  }

  function buildRefresh() {
    var button = $("[data-refresh]");
    if (!button) return;

    button.addEventListener("click", function () {
      button.disabled = true;
      button.classList.add("is-spinning");
      button.textContent = "Refreshing\u2026";
      setTimeout(function () {
        // Re-pull "fresh" metadata: re-decorate and re-render.
        renderBacklog();
        button.disabled = false;
        button.classList.remove("is-spinning");
        button.textContent = "Refresh backlog";
        toast("Backlog synced with Steam and IGDB");
      }, 1200);
    });
  }

  /* ------------------------------- boot -------------------------------- */

  function boot() {
    CATALOG.forEach(function (game) {
      game.cover = "https://cdn.cloudflare.steamstatic.com/steam/apps/" +
        game.id + "/library_600x900.jpg";
    });

    if (PAGE === "home") {
      renderHomeStats();
      renderTopPicks();
      renderSigninPreview();
    } else if (PAGE === "search") {
      buildSearch();
    } else if (PAGE === "backlog") {
      buildSortControls();
      buildRefresh();
      renderBacklog();
    }
  }

  boot();
})();