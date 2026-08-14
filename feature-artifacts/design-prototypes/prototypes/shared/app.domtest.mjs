/* Backlog Boss prototypes — DOM-shim interaction test for shared/app.js.
   Run from the prototypes/ dir:  node shared/app.domtest.mjs
   Verifies search/filter, the three sorts, add-to-backlog, complete+undo,
   remove+confirm, refresh, home stats, top picks, and sign-in preview. */

import { readFileSync } from "node:fs";

class FakeEl {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.attrs = {};
    this._text = "";
    this._classSet = new Set();
    this.dataset = {};
    this.style = {};
    this.handlers = {};
    this.value = "";
    this.disabled = false;
    this.parentNode = null;
  }
  set className(v) { this._classSet = new Set(String(v).split(/\s+/).filter(Boolean)); }
  get className() { return [...this._classSet].join(" "); }
  get classList() {
    return {
      add: (c) => this._classSet.add(c),
      remove: (c) => this._classSet.delete(c),
      toggle: (c, force) => {
        if (force === undefined) {
          this._classSet.has(c) ? this._classSet.delete(c) : this._classSet.add(c);
        } else {
          force ? this._classSet.add(c) : this._classSet.delete(c);
        }
      },
      contains: (c) => this._classSet.has(c),
    };
  }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k] ?? null; }
  set textContent(v) { this._text = String(v); }
  get textContent() { return this._text; }
  set innerHTML(v) { if (v === "") this.children = []; else throw new Error("innerHTML only supports clearing"); }
  get innerHTML() { return ""; }
  appendChild(c) { c.parentNode = this; this.children.push(c); return c; }
  append(...nodes) { nodes.forEach((n) => this.appendChild(n)); }
  remove() { if (this.parentNode) this.parentNode.children = this.parentNode.children.filter((c) => c !== this); }
  addEventListener(type, fn) { (this.handlers[type] ||= []).push(fn); }
  emit(type, ev = {}) { (this.handlers[type] || []).forEach((fn) => fn(ev)); }
  focus() {}
  querySelector(sel) { return match(this, sel, false); }
  querySelectorAll(sel) { return match(this, sel, true); }
}

const kebabToCamel = (n) => n.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
const matchAttr = (el, name, value) => {
  if (value !== undefined) return (el.attrs[name] ?? el.dataset[kebabToCamel(name.slice(5))]) === value;
  return name in el.attrs || (name.startsWith("data-") && el.dataset[kebabToCamel(name.slice(5))] !== undefined);
};
const matchClass = (el, cls) => el._classSet.has(cls);

function matchSelector(el, sel) {
  if (sel.startsWith("[")) {
    const m = sel.match(/^\[([\w-]+)(?:="([^"]*)")?\]$/);
    if (!m) throw new Error("unsupported selector " + sel);
    return matchAttr(el, m[1], m[2]);
  }
  if (sel.startsWith(".")) {
    const cls = sel.slice(1);
    if (cls.includes(" ")) return cls.split(/\s+/).every((c) => matchClass(el, c));
    return matchClass(el, cls);
  }
  if (sel.includes(".")) {
    const [tag, cls] = sel.split(".");
    return (tag ? el.tag === tag : true) && matchClass(el, cls);
  }
  return el.tag === sel;
}

function walk(el, pred, all, out) {
  if (pred(el)) { if (!all) return el; out.push(el); }
  for (const c of el.children) { const r = walk(c, pred, all, out); if (!all && r) return r; }
  return all ? null : null;
}

function match(root, sel, all) {
  const out = [];
  const hit = walk(root, (el) => el !== root && matchSelector(el, sel.trim()), all, out);
  return all ? out : hit;
}

const body = new FakeEl("body");
body.dataset = {};
const documentShim = {
  body,
  querySelector: (sel) => body.querySelector(sel),
  querySelectorAll: (sel) => body.querySelectorAll(sel),
  createElement: (tag) => new FakeEl(tag),
  createTextNode: (text) => ({ text }),
  createDocumentFragment: () => new FakeEl("#fragment"),
};

const storage = new Map();
globalThis.localStorage = {
  getItem: (k) => (storage.has(k) ? storage.get(k) : null),
  setItem: (k, v) => storage.set(k, String(v)),
  removeItem: (k) => storage.delete(k),
};
globalThis.document = documentShim;
globalThis.window = globalThis;

function app() {
  const gamesSrc = readFileSync("shared/games.js", "utf8");
  const appSrc = readFileSync("shared/app.js", "utf8");
  eval(gamesSrc + "\n" + appSrc); // eslint-disable-line no-eval
}

let failures = 0;
function assert(cond, msg) {
  if (cond) console.log("  ok  " + msg);
  else { failures++; console.log("  FAIL " + msg); }
}

function resetBody(dataset) {
  body.children = [];
  body.dataset = dataset;
  body._classSet.clear();
}
const textOf = (el) => (el ? el._text : null);

// first load primes the module-level SEED (and persists it to the storage stub)
resetBody({ site: "seed", page: "home" });
app();

/* ---------- HOME ---------- */
console.log("HOME:");
resetBody({ site: "test", page: "home" });
for (const k of ["active", "completed", "hours", "score"]) {
  const e = new FakeEl("div"); e.dataset.stat = k;
  body.appendChild(e);
}
const picks = new FakeEl("div"); picks.dataset.picks = ""; body.appendChild(picks);
const toggle = new FakeEl("button"); toggle.dataset.toggleSignin = ""; body.appendChild(toggle);
app();
assert(textOf(body.querySelector('[data-stat="active"]')) === "12", "active stat = 12");
assert(textOf(body.querySelector('[data-stat="completed"]')) === "3", "completed stat = 3");
assert(textOf(body.querySelector('[data-stat="hours"]')) === "365 h", "hours stat = 365 h");
assert(body.querySelector("[data-picks]").children.length === 3, "top picks renders 3 rows");
assert(toggle.handlers.click?.length === 1, "sign-in toggle wired");
toggle.emit("click");
assert(body._classSet.has("signin-preview"), "toggle adds signin-preview class");
toggle.emit("click");
assert(!body._classSet.has("signin-preview"), "toggle removes signin-preview class");

/* ---------- SEARCH ---------- */
console.log("SEARCH:");
resetBody({ site: "test", page: "search" });
const input = new FakeEl("input"); input.dataset.search = ""; body.appendChild(input);
const genres = new FakeEl("div"); genres.dataset.genres = ""; body.appendChild(genres);
const results = new FakeEl("div"); results.dataset.results = ""; body.appendChild(results);
const count = new FakeEl("p"); count.dataset.count = ""; body.appendChild(count);
const hint = new FakeEl("div"); hint.dataset.hint = ""; body.appendChild(hint);
app();
assert(results.children.length === 34, "catalog renders 34 rows with empty query");
assert(genres.children.length > 10, "genre chips built (" + genres.children.length + ")");
assert(results.querySelectorAll(".game-row").length === 34, "34 .game-row elements");
assert(results.querySelectorAll(".chip--in-backlog").length === 15, "15 seeded backlog badges in default list");
assert(textOf(count) === "34 games in the catalog", "count text");
input.value = "hades";
input.emit("input");
assert(results.children.length === 1, "filter 'hades' -> 1 row");
assert(results.children[0].querySelector(".chip--in-backlog"), "seeded game shows In backlog chip");
input.value = "half";
input.emit("input");
const addBtn = results.children[0].querySelector(".btn");
assert(addBtn && textOf(addBtn) === "Add to backlog", "add button present for non-backlog game");
addBtn.emit("click");
assert(results.children[0].querySelector(".chip--in-backlog"), "row now shows 'In backlog'");
assert(storage.has("bb-proto.test"), "backlog persisted to localStorage");
input.value = "zzz";
input.emit("input");
assert(textOf(results.children[0]) === "No games match \u201czzz\u201d. Try another title.", "empty-state message");
const genreFirst = genres.children[0];
genreFirst.emit("click");
input.value = "";
input.emit("input");
const allFiltered = results.querySelectorAll(".game-row");
assert(allFiltered.length > 0 && allFiltered.length < 34, "genre filter narrows results (" + allFiltered.length + ")");

/* ---------- BACKLOG ---------- */
console.log("BACKLOG:");
resetBody({ site: "test", page: "backlog" });
const sortBtns = ["score", "time", "blended"].map((s) => {
  const b = new FakeEl("button"); b.dataset.sort = s; body.appendChild(b); return b;
});
const refresh = new FakeEl("button"); refresh.dataset.refresh = ""; body.appendChild(refresh);
const activeMount = new FakeEl("div"); activeMount.dataset.bblist = "active"; body.appendChild(activeMount);
const completedMount = new FakeEl("div"); completedMount.dataset.bblist = "completed"; body.appendChild(completedMount);
const countActive = new FakeEl("span"); countActive.dataset.countActive = ""; body.appendChild(countActive);
const countCompleted = new FakeEl("span"); countCompleted.dataset.countCompleted = ""; body.appendChild(countCompleted);
const empty = new FakeEl("div"); empty.dataset.empty = ""; empty.classList.add("empty"); body.appendChild(empty);
app();
assert(activeMount.children.length === 13, "13 active rows (12 seeded + 1 added in search test)");
assert(completedMount.children.length === 3, "3 completed rows");
assert(textOf(countActive) === "13" && textOf(countCompleted) === "3", "counts filled");
assert(sortBtns[0]._classSet.has("is-active"), "score sort active by default");
const scoreFirst = activeMount.children[0].querySelector(".game-row__title").textContent;
assert(scoreFirst === "Elden Ring" || scoreFirst === "Baldur's Gate 3", "score sort: highest rating first (" + scoreFirst + ")");
sortBtns[1].emit("click");
const timeFirst = activeMount.children[0].querySelector(".game-row__title").textContent;
assert(timeFirst === "Vampire Survivors", "time sort: shortest first (" + timeFirst + ")");
sortBtns[2].emit("click");
assert(sortBtns[2]._classSet.has("is-active"), "blended sort active after click");
const completeBtn = activeMount.children[0].querySelector(".btn");
completeBtn.emit("click");
assert(activeMount.children.length === 12 && completedMount.children.length === 4, "mark complete moves row");
const undoBtn = documentShim.body.querySelector(".toast__action");
assert(undoBtn, "undo action present in toast");
undoBtn.emit("click");
assert(activeMount.children.length === 13 && completedMount.children.length === 3, "undo restores the row");
const removeBtn = activeMount.children[0].querySelectorAll(".btn")[1];
removeBtn.emit("click");
const modalConfirm = documentShim.body.querySelector(".modal")?.querySelector(".btn--danger");
assert(modalConfirm, "remove confirm modal shown");
modalConfirm.emit("click");
await new Promise((r) => setTimeout(r, 0));
assert(activeMount.children.length === 12, "confirmed remove deletes row");
refresh.emit("click");
assert(refresh.disabled === true, "refresh disables button while running");
setTimeout(() => {
  assert(refresh.disabled === false, "refresh re-enables button after sync");
  console.log("\n" + (failures === 0 ? "ALL CHECKS PASSED" : failures + " CHECKS FAILED"));
  process.exit(failures === 0 ? 0 : 1);
}, 1400);