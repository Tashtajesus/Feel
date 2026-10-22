"use strict";

// ---------- Хранилище ----------
const STORE_KEY = "feel-v1";
const MEALS = { breakfast: "Завтрак", lunch: "Обед", dinner: "Ужин", snack: "Перекус" };
const MEAL_ICONS = { breakfast: "🍳", lunch: "🍲", dinner: "🍽️", snack: "🍎" };
const OFF = "https://world.openfoodfacts.org";

const defaultState = () => ({
  profile: {
    sex: "m", age: 28, height: 178, weight: 75, activity: "1.375",
    neck: null, waist: null, hips: null, bodyFat: null,
    goal: "keep", targetWeight: null, pace: null,
  },
  targets: { kcal: 2300, p: 140, f: 75, c: 260, water: 2000 },
  entries: {},
  water: {},
  weights: [],
  recent: [],
  measurements: [],
});

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORE_KEY));
    if (saved) {
      const base = defaultState();
      return { ...base, ...saved, profile: { ...base.profile, ...saved.profile } };
    }
  } catch {}
  return defaultState();
}

let state = loadState();
function save() {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(state));
  } catch {
    toast("Не удалось сохранить: память браузера заполнена");
  }
}

// ---------- Утилиты ----------
const $ = (sel) => document.querySelector(sel);
const round = (n, d = 0) => Math.round(n * 10 ** d) / 10 ** d;
const esc = (s) => String(s).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]);
const norm = (s) => s.toLowerCase().replace(/ё/g, "е").trim();
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);

function dateKey(d) {
  const z = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}`;
}
function shiftDate(key, days) {
  const [y, m, d] = key.split("-").map(Number);
  return dateKey(new Date(y, m - 1, d + days));
}
const todayKey = () => dateKey(new Date());

function dayLabel(key) {
  const t = todayKey();
  if (key === t) return "Сегодня";
  if (key === shiftDate(t, -1)) return "Вчера";
  const [y, m, d] = key.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("ru-RU", { day: "numeric", month: "short", weekday: "short" });
}

function defaultMeal() {
  const h = new Date().getHours();
  if (h < 11) return "breakfast";
  if (h < 16) return "lunch";
  if (h < 21) return "dinner";
  return "snack";
}

let toastTimer;
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.hidden = true), 2600);
}

function scale(food, grams) {
  const k = grams / 100;
  return { kcal: round(food.kcal * k), p: round(food.p * k, 1), f: round(food.f * k, 1), c: round(food.c * k, 1) };
}

// ---------- Навигация ----------
let currentDay = todayKey();
let currentView = "today";

document.querySelectorAll(".tab").forEach((tab) =>
  tab.addEventListener("click", () => showView(tab.dataset.view))
);

function showView(name) {
  currentView = name;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.view === name));
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== `view-${name}`));
  if (name === "today") renderToday();
  if (name === "stats") renderStats();
  if (name === "profile") renderProfile();
  window.scrollTo(0, 0);
}

$("#prev-day").addEventListener("click", () => { currentDay = shiftDate(currentDay, -1); renderToday(); });
$("#next-day").addEventListener("click", () => {
  if (currentDay < todayKey()) { currentDay = shiftDate(currentDay, 1); renderToday(); }
});
$("#day-label").addEventListener("click", () => { currentDay = todayKey(); renderToday(); });

// ---------- Листы (bottom sheets) ----------
function openSheet(id) { $(id).hidden = false; }
function closeSheet(id) {
  $(id).hidden = true;
  if (id === "#barcode-sheet") stopScanner();
}
document.querySelectorAll(".sheet-backdrop").forEach((bd) => {
  bd.addEventListener("click", (e) => {
    if (e.target === bd || e.target.closest("[data-close]")) closeSheet(`#${bd.id}`);
  });
});
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  const open = [...document.querySelectorAll(".sheet-backdrop")].filter((b) => !b.hidden).pop();
  if (open) closeSheet(`#${open.id}`);
});

$("#fab").addEventListener("click", () => {
  $("#meal-select").value = defaultMeal();
  openSheet("#add-menu");
});
const selectedMeal = () => $("#meal-select").value;

// ---------- Записи ----------
function dayEntries(key = currentDay) {
  return state.entries[key] || [];
}

function addEntry(entry) {
  const list = (state.entries[currentDay] ||= []);
  list.push({ id: uid(), meal: selectedMeal(), time: Date.now(), ...entry });
  save();
  renderToday();
}

function rememberFood(food) {
  state.recent = [food, ...state.recent.filter((r) => r.name !== food.name)].slice(0, 20);
  save();
}

function totals(entries) {
  return entries.reduce(
    (t, e) => ({ kcal: t.kcal + e.kcal, p: t.p + e.p, f: t.f + e.f, c: t.c + e.c }),
    { kcal: 0, p: 0, f: 0, c: 0 }
  );
}

// ---------- Экран «Сегодня» ----------
function renderToday() {
  $("#day-label").textContent = dayLabel(currentDay);
  $("#next-day").style.visibility = currentDay < todayKey() ? "visible" : "hidden";

  const entries = dayEntries();
  const t = totals(entries);
  const g = state.targets;
  const left = g.kcal - t.kcal;

  $("#kcal-left").textContent = Math.abs(round(left));
  $("#kcal-left").classList.toggle("over", left < 0);
  $("#kcal-left-label").textContent = left < 0 ? "ккал сверх нормы" : "ккал осталось";
  $("#kcal-eaten").textContent = round(t.kcal);
  $("#kcal-goal").textContent = g.kcal;
  const ratio = Math.min(t.kcal / g.kcal, 1);
  const ring = $("#kcal-ring");
  ring.style.strokeDashoffset = 314.16 * (1 - ratio);
  ring.classList.toggle("over", left < 0);

  for (const m of ["p", "c", "f"]) {
    const rest = g[m] - t[m];
    $(`#${m}-left`).textContent = rest < 0 ? `+${round(-rest)}` : round(rest);
    $(`#${m}-bar`).style.width = `${Math.min((t[m] / g[m]) * 100, 100)}%`;
  }

  const water = state.water[currentDay] || 0;
  $("#water-ml").textContent = water;
  $("#water-goal").textContent = g.water;

  const box = $("#meals");
  if (!entries.length) {
    box.innerHTML = `<div class="card empty"><b>Пока пусто</b>Нажмите «+», чтобы сфотографировать еду или найти продукт в базе</div>`;
    return;
  }
  box.innerHTML = Object.entries(MEALS)
    .map(([key, title]) => {
      const list = entries.filter((e) => e.meal === key);
      if (!list.length) return "";
      const sum = totals(list);
      return `<div class="meal-block">
        <div class="meal-head"><span>${title}</span><span>${round(sum.kcal)} ккал</span></div>
        ${list.map(entryHtml).join("")}
      </div>`;
    })
    .join("");
}

function entryHtml(e) {
  const thumb = e.photo
    ? `<img class="entry-thumb" src="${e.photo}" alt="">`
    : `<div class="entry-thumb">${MEAL_ICONS[e.meal] || "🍽️"}</div>`;
  const time = new Date(e.time).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  return `<div class="card entry">
    ${thumb}
    <div class="entry-body">
      <div class="entry-name">${esc(e.name)}</div>
      <div class="entry-kcal">🔥 ${round(e.kcal)} ккал <span class="muted small">· ${e.grams ? `${round(e.grams)} г · ` : ""}${time}</span></div>
      <div class="entry-macros">
        <span><i class="dot" style="background:var(--protein)"></i>${round(e.p)} б</span>
        <span><i class="dot" style="background:var(--carbs)"></i>${round(e.c)} у</span>
        <span><i class="dot" style="background:var(--fat)"></i>${round(e.f)} ж</span>
      </div>
    </div>
    <button class="entry-del" data-del="${e.id}" aria-label="Удалить">×</button>
  </div>`;
}

$("#meals").addEventListener("click", (e) => {
  const id = e.target.closest("[data-del]")?.dataset.del;
  if (!id) return;
  state.entries[currentDay] = dayEntries().filter((x) => x.id !== id);
  save();
  renderToday();
  toast("Запись удалена");
});

$("#water-plus").addEventListener("click", () => {
  state.water[currentDay] = (state.water[currentDay] || 0) + 250;
  save();
  renderToday();
});
$("#water-minus").addEventListener("click", () => {
  state.water[currentDay] = Math.max(0, (state.water[currentDay] || 0) - 250);
  save();
  renderToday();
});

// ---------- Фото: распознавание через ИИ ----------
let photoData = null; // { image, mediaType, thumb }
let photoResult = null;

$("#camera-input").addEventListener("change", onPhotoPicked);
$("#gallery-input").addEventListener("change", onPhotoPicked);

async function onPhotoPicked(e) {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  closeSheet("#add-menu");
  try {
    const img = await loadImage(file);
    photoData = {
      image: toJpegBase64(img, 1024, 0.85),
      mediaType: "image/jpeg",
      thumb: `data:image/jpeg;base64,${toJpegBase64(img, 160, 0.7)}`,
    };
    $("#photo-preview").src = `data:image/jpeg;base64,${photoData.image}`;
    $("#photo-hint").value = "";
    openSheet("#photo-sheet");
    analyze();
  } catch {
    toast("Не удалось открыть изображение");
  }
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
    img.onerror = reject;
    img.src = url;
  });
}

function toJpegBase64(img, maxSide, quality) {
  const k = Math.min(1, maxSide / Math.max(img.naturalWidth, img.naturalHeight));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(img.naturalWidth * k);
  canvas.height = Math.round(img.naturalHeight * k);
  canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", quality).split(",")[1];
}

const CODE_KEY = "feel-access-code";
function getAccessCode() {
  try {
    return localStorage.getItem(CODE_KEY) || "";
  } catch {
    return "";
  }
}
function askAccessCode() {
  const code = prompt("Введите код доступа к распознаванию фото:");
  if (!code) return false;
  try {
    localStorage.setItem(CODE_KEY, code.trim());
  } catch {}
  return true;
}

async function analyze() {
  photoResult = null;
  $("#scan-overlay").classList.add("on");
  $("#photo-status").textContent = "Анализирую фото…";
  $("#photo-items").innerHTML = "";
  $("#photo-total").innerHTML = "";
  $("#photo-save").disabled = true;
  $("#reanalyze").disabled = true;
  try {
    const send = () =>
      fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Access-Code": getAccessCode() },
        body: JSON.stringify({ image: photoData.image, mediaType: photoData.mediaType, hint: $("#photo-hint").value }),
      });
    let res = await send();
    let data = await res.json().catch(() => ({}));
    if (res.status === 401 && data.needCode && askAccessCode()) {
      res = await send();
      data = await res.json().catch(() => ({}));
    }
    if (!res.ok) throw new Error(data.error || `Ошибка сервера (${res.status})`);
    photoResult = {
      dish: data.dish,
      note: data.note,
      confidence: data.confidence,
      items: data.items.map((it) => ({
        name: it.name,
        grams: Math.max(1, round(it.grams)),
        kcal: it.kcal_per_100g, p: it.protein_per_100g, f: it.fat_per_100g, c: it.carbs_per_100g,
      })),
    };
    renderPhotoResult();
  } catch (err) {
    $("#photo-status").innerHTML = `⚠️ ${esc(err.message === "Failed to fetch" ? "Нет связи с сервером" : err.message)}`;
  } finally {
    $("#scan-overlay").classList.remove("on");
    $("#reanalyze").disabled = false;
  }
}

const CONFIDENCE = { low: "низкая", medium: "средняя", high: "высокая" };

function renderPhotoResult() {
  const r = photoResult;
  $("#photo-status").innerHTML = `${esc(r.dish || "Результат")}
    <span class="note">Точность: ${CONFIDENCE[r.confidence] || "—"}${r.note ? ` · ${esc(r.note)}` : ""}</span>`;
  $("#photo-items").innerHTML = r.items
    .map((it, i) => {
      const s = scale(it, it.grams);
      return `<div class="photo-item" data-i="${i}">
        <input class="name" value="${esc(it.name)}" aria-label="Название">
        <input class="grams" type="number" min="1" inputmode="decimal" value="${it.grams}" aria-label="Граммы">
        <span class="kcal">${s.kcal} ккал</span>
        <button class="rm" data-rm="${i}" aria-label="Убрать">×</button>
        <span class="sub">${subLine(it, s)}</span>
      </div>`;
    })
    .join("");
  updatePhotoTotal();
}

const subLine = (it, s) => `Б ${s.p} · Ж ${s.f} · У ${s.c} · ${round(it.kcal)} ккал/100 г`;

function updatePhotoTotal() {
  const sums = photoResult.items.map((it) => scale(it, it.grams));
  const t = totals(sums);
  $("#photo-total").innerHTML = photoResult.items.length
    ? `<span>Итого</span><span>${round(t.kcal)} ккал</span>`
    : "";
  $("#photo-save").disabled = !photoResult.items.length;
  return t;
}

$("#photo-items").addEventListener("input", (e) => {
  const row = e.target.closest(".photo-item");
  if (!row) return;
  const it = photoResult.items[row.dataset.i];
  if (e.target.classList.contains("name")) it.name = e.target.value;
  if (e.target.classList.contains("grams")) {
    it.grams = Math.max(0, Number(e.target.value) || 0);
    const s = scale(it, it.grams);
    row.querySelector(".kcal").textContent = `${s.kcal} ккал`;
    row.querySelector(".sub").textContent = subLine(it, s);
    updatePhotoTotal();
  }
});
$("#photo-items").addEventListener("click", (e) => {
  const i = e.target.closest("[data-rm]")?.dataset.rm;
  if (i === undefined) return;
  photoResult.items.splice(Number(i), 1);
  renderPhotoResult();
});
$("#reanalyze").addEventListener("click", () => photoData && analyze());

$("#photo-save").addEventListener("click", () => {
  const items = photoResult.items.filter((it) => it.grams > 0);
  const t = totals(items.map((it) => scale(it, it.grams)));
  const grams = items.reduce((s, it) => s + it.grams, 0);
  const name = photoResult.dish || items.map((it) => it.name).join(", ");
  addEntry({ name, grams, photo: photoData.thumb, source: "photo", items, ...t });
  closeSheet("#photo-sheet");
  toast(`Добавлено: ${round(t.kcal)} ккал`);
});

// ---------- База продуктов ----------
let activeGroup = null;
let onlineResults = [];

$("#open-search").addEventListener("click", () => {
  closeSheet("#add-menu");
  $("#search-input").value = "";
  activeGroup = null;
  onlineResults = [];
  renderChips();
  renderSearch();
  openSheet("#search-sheet");
  setTimeout(() => $("#search-input").focus(), 250);
});

function renderChips() {
  const groups = ["Недавние", ...Object.keys(FOOD_GROUPS)];
  $("#group-chips").innerHTML = groups
    .map((g) => `<button class="chip ${g === (activeGroup || "Недавние") ? "active" : ""}" data-group="${esc(g)}">${esc(g)}</button>`)
    .join("");
}
$("#group-chips").addEventListener("click", (e) => {
  const g = e.target.closest("[data-group]")?.dataset.group;
  if (!g) return;
  activeGroup = g === "Недавние" ? null : g;
  $("#search-input").value = "";
  onlineResults = [];
  renderChips();
  renderSearch();
});

let searchTimer;
$("#search-input").addEventListener("input", () => {
  clearTimeout(searchTimer);
  onlineResults = [];
  searchTimer = setTimeout(renderSearch, 120);
});
$("#search-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") searchOnline();
});

function localSearch(q) {
  const words = norm(q).split(/\s+/).filter(Boolean);
  return FOODS
    .map((f) => {
      const n = norm(f.name);
      if (!words.every((w) => n.includes(w))) return null;
      return { f, score: (n.startsWith(words[0]) ? 0 : 1) + n.length / 100 };
    })
    .filter(Boolean)
    .sort((a, b) => a.score - b.score)
    .map((x) => x.f);
}

let listed = [];
function renderSearch() {
  const q = $("#search-input").value.trim();
  let list;
  let emptyMsg = "Ничего не найдено в локальной базе — попробуйте мировую базу ниже";
  if (q) {
    const local = localSearch(q);
    const recent = state.recent.filter((r) => norm(r.name).includes(norm(q)) && !local.some((l) => l.name === r.name));
    list = [...recent, ...local, ...onlineResults];
  } else if (activeGroup) {
    list = FOODS.filter((f) => f.group === activeGroup);
  } else {
    list = state.recent;
    emptyMsg = "Здесь появятся продукты, которые вы добавляли. Начните вводить название.";
  }
  listed = list.slice(0, 80);
  $("#search-results").innerHTML = listed.length
    ? listed.map((f, i) => `<button class="food-row" data-i="${i}">
        <div>
          <div class="food-name">${esc(f.name)}${f.source === "off" ? '<span class="src-tag">OFF</span>' : ""}</div>
          <div class="food-meta">${f.brand ? `${esc(f.brand)} · ` : ""}Б ${round(f.p, 1)} · Ж ${round(f.f, 1)} · У ${round(f.c, 1)} на 100 г</div>
        </div>
        <div class="food-kcal">${round(f.kcal)} ккал</div>
      </button>`).join("")
    : `<p class="empty">${emptyMsg}</p>`;
  $("#search-online").hidden = !q;
}

$("#search-results").addEventListener("click", (e) => {
  const i = e.target.closest("[data-i]")?.dataset.i;
  if (i !== undefined) openPortion(listed[i]);
});

$("#search-online").addEventListener("click", searchOnline);

function fromOff(p) {
  const n = p.nutriments || {};
  const kcal = n["energy-kcal_100g"] ?? (n["energy_100g"] ? n["energy_100g"] / 4.184 : undefined);
  if (!p.product_name || kcal === undefined) return null;
  return {
    name: p.product_name.trim(),
    brand: (p.brands || "").split(",")[0].trim(),
    kcal: Number(kcal) || 0,
    p: Number(n.proteins_100g) || 0,
    f: Number(n.fat_100g) || 0,
    c: Number(n.carbohydrates_100g) || 0,
    serving: Number(p.serving_quantity) || null,
    source: "off",
  };
}

async function searchOnline() {
  const q = $("#search-input").value.trim();
  if (!q) return;
  const btn = $("#search-online");
  btn.disabled = true;
  btn.textContent = "Ищу в Open Food Facts…";
  try {
    const url = `${OFF}/cgi/search.pl?search_terms=${encodeURIComponent(q)}&search_simple=1&action=process&json=1&page_size=30&fields=product_name,brands,nutriments,serving_quantity`;
    const res = await fetch(url);
    const data = await res.json();
    onlineResults = (data.products || []).map(fromOff).filter(Boolean);
    renderSearch();
    if (!onlineResults.length) toast("В мировой базе тоже ничего — добавьте вручную");
  } catch {
    toast("Мировая база недоступна, проверьте интернет");
  } finally {
    btn.disabled = false;
    btn.textContent = "Искать в мировой базе Open Food Facts";
  }
}

// ---------- Порция ----------
let portionFood = null;

function openPortion(food) {
  portionFood = food;
  $("#portion-name").textContent = food.brand ? `${food.name} · ${food.brand}` : food.name;
  $("#portion-per100").textContent = `На 100 г: ${round(food.kcal)} ккал · Б ${round(food.p, 1)} · Ж ${round(food.f, 1)} · У ${round(food.c, 1)}`;
  const presets = [50, 100, 150, 200, 250, 300];
  if (food.serving && !presets.includes(food.serving)) presets.unshift(food.serving);
  $("#portion-presets").innerHTML = presets.map((g) => `<button class="chip" data-g="${g}">${g === food.serving ? `порция ${g}` : g} г</button>`).join("");
  $("#portion-grams").value = food.lastGrams || food.serving || 100;
  updatePortion();
  openSheet("#portion-sheet");
}

function updatePortion() {
  const g = Number($("#portion-grams").value) || 0;
  const s = scale(portionFood, g);
  $("#portion-result").innerHTML = `
    <div><b>${s.kcal}</b><span>ккал</span></div>
    <div><b>${s.p}</b><span>белки</span></div>
    <div><b>${s.f}</b><span>жиры</span></div>
    <div><b>${s.c}</b><span>углев.</span></div>`;
}
$("#portion-grams").addEventListener("input", updatePortion);
$("#portion-presets").addEventListener("click", (e) => {
  const g = e.target.closest("[data-g]")?.dataset.g;
  if (!g) return;
  $("#portion-grams").value = g;
  updatePortion();
});
document.querySelectorAll("#portion-sheet [data-step]").forEach((b) =>
  b.addEventListener("click", () => {
    const input = $("#portion-grams");
    input.value = Math.max(1, (Number(input.value) || 0) + Number(b.dataset.step));
    updatePortion();
  })
);
$("#portion-save").addEventListener("click", () => {
  const g = Number($("#portion-grams").value);
  if (!(g > 0)) return toast("Укажите вес порции");
  const s = scale(portionFood, g);
  const { name, brand, kcal, p, f, c, serving, source } = portionFood;
  rememberFood({ name, brand, kcal, p, f, c, serving, source, lastGrams: g });
  addEntry({ name: brand ? `${name} (${brand})` : name, grams: g, source, ...s });
  closeSheet("#portion-sheet");
  closeSheet("#search-sheet");
  closeSheet("#barcode-sheet");
  toast(`Добавлено: ${s.kcal} ккал`);
});

// ---------- Штрихкод ----------
let scanStream = null;
let scanLoop = null;

$("#open-barcode").addEventListener("click", async () => {
  closeSheet("#add-menu");
  $("#barcode-input").value = "";
  openSheet("#barcode-sheet");
  const status = $("#barcode-status");
  if (!("BarcodeDetector" in window) || !navigator.mediaDevices?.getUserMedia) {
    status.textContent = "Камера-сканер не поддерживается этим браузером — введите цифры штрихкода вручную.";
    return;
  }
  try {
    const detector = new BarcodeDetector({ formats: ["ean_13", "ean_8", "upc_a", "upc_e"] });
    scanStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    const video = $("#barcode-video");
    video.srcObject = scanStream;
    video.hidden = false;
    await video.play();
    status.textContent = "Наведите камеру на штрихкод";
    scanLoop = setInterval(async () => {
      const codes = await detector.detect(video).catch(() => []);
      if (codes[0]) {
        $("#barcode-input").value = codes[0].rawValue;
        stopScanner();
        lookupBarcode(codes[0].rawValue);
      }
    }, 300);
  } catch {
    status.textContent = "Нет доступа к камере — введите цифры штрихкода вручную.";
  }
});

function stopScanner() {
  clearInterval(scanLoop);
  scanStream?.getTracks().forEach((t) => t.stop());
  scanStream = null;
  $("#barcode-video").hidden = true;
}

$("#barcode-form").addEventListener("submit", (e) => {
  e.preventDefault();
  stopScanner();
  lookupBarcode($("#barcode-input").value.trim());
});

async function lookupBarcode(code) {
  const status = $("#barcode-status");
  status.textContent = `Ищу ${code}…`;
  try {
    const res = await fetch(`${OFF}/api/v2/product/${encodeURIComponent(code)}.json?fields=product_name,brands,nutriments,serving_quantity`);
    const data = await res.json();
    const food = data.status === 1 ? fromOff(data.product) : null;
    if (!food) {
      status.textContent = "Продукт не найден в базе. Добавьте его вручную по этикетке.";
      return;
    }
    status.textContent = "";
    openPortion(food);
  } catch {
    status.textContent = "База недоступна, проверьте интернет.";
  }
}

// ---------- Ручной ввод ----------
$("#open-manual").addEventListener("click", () => {
  closeSheet("#add-menu");
  $("#manual-form").reset();
  openSheet("#manual-sheet");
});
$("#manual-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const num = (k) => Math.max(0, Number(fd.get(k)) || 0);
  addEntry({ name: fd.get("name").trim(), kcal: num("kcal"), p: num("p"), f: num("f"), c: num("c"), grams: num("grams") || null, source: "manual" });
  closeSheet("#manual-sheet");
  toast("Добавлено");
});

// ---------- Профиль и расчёт нормы ----------
const KCAL_PER_KG = 7700; // энергия 1 кг жировой ткани
const PACE = { lose: { min: 0.1, max: 1, def: 0.5 }, gain: { min: 0.1, max: 0.5, def: 0.25 } };
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const fmtDate = (key) => key.slice(5).split("-").reverse().join(".");

function renderProfile() {
  const els = $("#profile-form").elements;
  for (const [k, v] of Object.entries(state.profile)) if (els[k]) els[k].value = v ?? "";
  const tf = $("#targets-form");
  for (const [k, v] of Object.entries(state.targets)) if (tf.elements[k]) tf.elements[k].value = v;
  syncProfileForm();
}

function readProfile() {
  const els = $("#profile-form").elements;
  const num = (k) => {
    const v = parseFloat(els[k].value);
    return Number.isFinite(v) ? v : null;
  };
  return {
    sex: els.sex.value || "m",
    age: num("age"),
    height: num("height"),
    weight: num("weight"),
    activity: els.activity.value,
    neck: num("neck"),
    waist: num("waist"),
    hips: num("hips"),
    bodyFat: num("bodyFat"),
    goal: els.goal.value || "keep",
    targetWeight: num("targetWeight"),
    pace: num("pace"),
  };
}

function syncProfileForm() {
  const p = state.profile;
  const els = $("#profile-form").elements;
  $("#hips-label").hidden = p.sex !== "f";
  $("#goal-extra").hidden = p.goal === "keep";
  if (p.goal !== "keep") {
    const range = PACE[p.goal];
    els.pace.min = range.min;
    els.pace.max = range.max;
    els.pace.value = clamp(p.pace ?? range.def, range.min, range.max);
    const pct = p.weight ? ` · ${round((els.pace.value / p.weight) * 100, 1)}% веса` : "";
    $("#pace-out").textContent = `${els.pace.value} кг в неделю${pct}`;
  }
  renderPlan(computePlan(p));
}

$("#profile-form").addEventListener("input", (e) => {
  const prevGoal = state.profile.goal;
  state.profile = { ...state.profile, ...readProfile() };
  if (state.profile.goal !== prevGoal && state.profile.goal !== "keep") state.profile.pace = PACE[state.profile.goal].def;
  save();
  syncProfileForm();
});
$("#profile-form").addEventListener("submit", (e) => e.preventDefault());

// Формула ВМС США: % жира по обхватам шеи, талии (и бёдер у женщин) и росту.
function bodyFatNavy({ sex, height, neck, waist, hips }) {
  if (!height || !neck || !waist) return null;
  if (sex === "m") {
    if (waist <= neck) return null;
    return 495 / (1.0324 - 0.19077 * Math.log10(waist - neck) + 0.15456 * Math.log10(height)) - 450;
  }
  if (!hips || waist + hips <= neck) return null;
  return 495 / (1.29579 - 0.35004 * Math.log10(waist + hips - neck) + 0.221 * Math.log10(height)) - 450;
}

const COLORS = { good: "var(--good)", mid: "var(--carbs)", bad: "var(--danger)", low: "var(--fat)" };

function bmiClass(bmi) {
  if (bmi < 18.5) return ["Дефицит массы", "low"];
  if (bmi < 25) return ["Норма", "good"];
  if (bmi < 30) return ["Избыточный вес", "mid"];
  return ["Ожирение", "bad"];
}

function fatClass(bf, sex) {
  const t = sex === "m" ? [6, 14, 18, 25] : [14, 21, 25, 32];
  if (bf < t[0]) return ["Ниже нормы", "low"];
  if (bf < t[1]) return ["Спортивный", "good"];
  if (bf < t[2]) return ["Фитнес", "good"];
  if (bf < t[3]) return ["Средний", "mid"];
  return ["Высокий", "bad"];
}

function computePlan(p) {
  if (!(p.age && p.height && p.weight)) return null;
  const warnings = [];
  const h2 = (p.height / 100) ** 2;
  const bmi = p.weight / h2;

  let bf = p.bodyFat;
  let bfSource = bf ? "введено вручную" : null;
  if (!bf) {
    const navy = bodyFatNavy(p);
    if (navy > 2 && navy < 70) {
      bf = navy;
      bfSource = "по замерам";
    } else if (p.neck || p.waist || p.hips) {
      warnings.push(["mid", p.sex === "f" ? "Для расчёта % жира нужны шея, талия и бёдра." : "Для расчёта % жира нужны шея и талия (талия больше шеи)."]);
    }
  }
  const lbm = bf ? p.weight * (1 - bf / 100) : null;

  // С известным % жира точнее Кэтч — МакАрдл (считает от сухой массы), иначе Миффлин — Сан Жеор.
  const mifflin = 10 * p.weight + 6.25 * p.height - 5 * p.age + (p.sex === "m" ? 5 : -161);
  const bmr = lbm ? 370 + 21.6 * lbm : mifflin;
  const formula = lbm ? "Кэтч — МакАрдл" : "Миффлин — Сан Жеор";
  const tdee = bmr * Number(p.activity);

  let delta = 0;
  let pace = 0;
  if (p.goal !== "keep") {
    const range = PACE[p.goal];
    pace = clamp(p.pace ?? range.def, range.min, range.max);
    delta = ((p.goal === "lose" ? -1 : 1) * pace * KCAL_PER_KG) / 7;
    if (p.goal === "lose" && pace > p.weight * 0.01) {
      warnings.push(["bad", "Темп быстрее 1% веса в неделю: велик риск потерять мышцы и сорваться. Лучше выбрать темп помедленнее."]);
    }
  }

  let kcal = tdee + delta;
  const floor = Math.round(Math.max(p.sex === "m" ? 1500 : 1200, bmr * 0.9) / 10) * 10;
  if (kcal < floor) {
    warnings.push(["bad", `При таком темпе вышло бы ${round(kcal)} ккал — слишком мало. Норма поднята до безопасных ${floor} ккал, цель будет достигнута позже.`]);
    kcal = floor;
  }
  kcal = Math.round(kcal / 10) * 10;
  const realDelta = kcal - tdee;

  // Белок: от сухой массы, если она известна; при ожирении — от веса при ИМТ 25, чтобы не завышать.
  const refWeight = bmi >= 30 ? 25 * h2 : p.weight;
  const protein = Math.round(lbm ? lbm * (p.goal === "lose" ? 2.3 : 2) : refWeight * { lose: 2, keep: 1.6, gain: 1.8 }[p.goal]);
  let fat = Math.round(Math.max((kcal * 0.27) / 9, refWeight * 0.7));
  let carbs = Math.round((kcal - protein * 4 - fat * 9) / 4);
  if (carbs < 50) {
    carbs = 50;
    fat = Math.max(0, Math.round((kcal - protein * 4 - carbs * 4) / 9));
  }

  const healthy = [round(18.5 * h2, 1), round(24.9 * h2, 1)];
  let eta = null;
  if (p.goal !== "keep" && p.targetWeight) {
    const diff = p.targetWeight - p.weight;
    if ((p.goal === "lose" && diff >= 0) || (p.goal === "gain" && diff <= 0)) {
      warnings.push(["mid", p.goal === "lose" ? "Желаемый вес не меньше текущего — проверьте цель." : "Желаемый вес не больше текущего — проверьте цель."]);
    } else {
      const weeklyKg = (Math.abs(realDelta) * 7) / KCAL_PER_KG;
      const weeks = Math.abs(diff) / weeklyKg;
      eta = { weeks: Math.ceil(weeks), date: shiftDate(todayKey(), Math.ceil(weeks * 7)), kg: Math.abs(round(diff, 1)) };
      if (p.targetWeight < healthy[0]) warnings.push(["bad", `Желаемый вес ниже здорового диапазона для вашего роста (от ${healthy[0]} кг).`]);
    }
  }
  if (p.goal === "gain" && bf && bf >= (p.sex === "m" ? 25 : 32)) {
    warnings.push(["mid", "При высоком % жира набор массы даст в основном жир. Часто выгоднее сначала «рекомпозиция»: поддержание веса + силовые тренировки + много белка."]);
  }
  if (p.age < 18) warnings.push(["mid", "Для подростков формулы неточны — дефицит калорий лучше согласовать с врачом."]);

  return {
    bmi, bf, bfSource, lbm, bmr, tdee, formula, kcal, delta: realDelta, pace,
    protein, fat, carbs, healthy, eta, warnings,
    whtr: p.waist ? p.waist / p.height : null,
    water: Math.round((p.weight * 30) / 250) * 250,
  };
}

let currentPlan = null;

function renderPlan(plan) {
  currentPlan = plan;
  $("#apply-targets").disabled = !plan;
  if (!plan) {
    $("#body-stats").innerHTML = `<p class="muted small">Заполните возраст, рост и вес.</p>`;
    $("#calc-target").hidden = true;
    $("#calc-warnings").innerHTML = "";
    $("#calc-formula").textContent = "";
    return;
  }
  const sex = state.profile.sex;
  const stat = (k, v, [label, tone] = []) =>
    `<div class="stat"><span class="k">${k}</span><b>${v}</b>${label ? `<span class="tag" style="--c:${COLORS[tone]}">${label}</span>` : ""}</div>`;
  const whtrClass = (r) => (r < 0.4 ? ["Низкий", "low"] : r < 0.5 ? ["Норма", "good"] : r < 0.6 ? ["Повышенный риск", "mid"] : ["Высокий риск", "bad"]);

  $("#calc-formula").textContent = plan.formula;
  $("#body-stats").innerHTML = [
    stat("Индекс массы тела", round(plan.bmi, 1), bmiClass(plan.bmi)),
    plan.bf
      ? stat(`% жира (${plan.bfSource})`, `${round(plan.bf, 1)}%`, fatClass(plan.bf, sex))
      : stat("% жира", "—", ["добавьте замеры", "mid"]),
    stat("Сухая масса тела", plan.lbm ? `${round(plan.lbm, 1)} кг` : "—"),
    stat("Талия / рост", plan.whtr ? round(plan.whtr, 2) : "—", plan.whtr ? whtrClass(plan.whtr) : undefined),
    stat("Базовый обмен", `${round(plan.bmr)} ккал`),
    stat("Расход за день", `${round(plan.tdee)} ккал`),
    stat("Здоровый вес для роста", `${plan.healthy[0]}–${plan.healthy[1]} кг`),
    stat("Вода", `${plan.water} мл`),
  ].join("");

  const d = round(plan.delta);
  const deltaText = Math.abs(d) < 20 ? "Поддержание веса" : d < 0 ? `Дефицит ${-d} ккал в день` : `Профицит ${d} ккал в день`;
  let etaText = "";
  if (plan.eta) {
    const [y, m, dd] = plan.eta.date.split("-").map(Number);
    const date = new Date(y, m - 1, dd).toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
    etaText = `<div class="line">${state.profile.goal === "lose" ? "−" : "+"}${plan.eta.kg} кг ≈ за ${plan.eta.weeks} нед. — к ${date}</div>`;
  }
  $("#calc-target").hidden = false;
  $("#calc-target").innerHTML = `
    <div class="line">Ваша дневная норма</div>
    <div class="big">${plan.kcal} ккал</div>
    <div class="line">${deltaText}</div>
    ${etaText}
    <div class="macro-row">
      <div><b>${plan.protein} г</b>белки</div>
      <div><b>${plan.fat} г</b>жиры</div>
      <div><b>${plan.carbs} г</b>углеводы</div>
    </div>`;
  $("#calc-warnings").innerHTML = plan.warnings.map(([t, msg]) => `<div class="warn ${t === "bad" ? "bad" : ""}">${esc(msg)}</div>`).join("");
}

$("#apply-targets").addEventListener("click", () => {
  const plan = currentPlan;
  if (!plan) return;
  const p = state.profile;
  const date = todayKey();
  state.targets = { kcal: plan.kcal, p: plan.protein, f: plan.fat, c: plan.carbs, water: plan.water };
  const lastWeight = state.weights[state.weights.length - 1];
  if (!lastWeight || lastWeight.kg !== p.weight) {
    state.weights = [...state.weights.filter((x) => x.date !== date), { date, kg: p.weight }].sort((a, b) => a.date.localeCompare(b.date));
  }
  if (p.waist || p.neck || p.hips || plan.bf) {
    const m = { date, neck: p.neck, waist: p.waist, hips: p.sex === "f" ? p.hips : null, bf: plan.bf ? round(plan.bf, 1) : null };
    state.measurements = [...state.measurements.filter((x) => x.date !== date), m].sort((a, b) => a.date.localeCompare(b.date));
  }
  save();
  renderProfile();
  toast(`Норма ${plan.kcal} ккал применена`);
});

$("#targets-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  state.targets = Object.fromEntries(["kcal", "p", "f", "c", "water"].map((k) => [k, Number(fd.get(k))]));
  save();
  toast("Норма сохранена");
});

$("#export-btn").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `feel-${todayKey()}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
});
$("#import-input").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  try {
    const data = JSON.parse(await file.text());
    if (typeof data !== "object" || !data.entries) throw new Error();
    const base = defaultState();
    state = { ...base, ...data, profile: { ...base.profile, ...data.profile } };
    save();
    renderProfile();
    toast("Данные импортированы");
  } catch {
    toast("Это не файл экспорта Feel");
  }
});

// ---------- Прогресс ----------
function barChart(values, labels, goal) {
  const W = 320, H = 150, pad = 18;
  const max = Math.max(goal || 0, ...values, 1) * 1.1;
  const bw = (W - pad * 2) / values.length;
  const y = (v) => H - pad - (v / max) * (H - pad * 2);
  const bars = values
    .map((v, i) => {
      const x = pad + i * bw + bw * 0.2;
      const h = H - pad - y(v);
      const over = goal && v > goal;
      return `<rect x="${x}" y="${y(v)}" width="${bw * 0.6}" height="${Math.max(h, v ? 2 : 0)}" rx="5" fill="${over ? "var(--danger)" : "var(--accent)"}" opacity="${v ? 1 : 0.15}"/>
        <text x="${x + bw * 0.3}" y="${H - 4}" text-anchor="middle">${labels[i]}</text>`;
    })
    .join("");
  const goalLine = goal
    ? `<line x1="${pad}" x2="${W - pad}" y1="${y(goal)}" y2="${y(goal)}" stroke="var(--muted)" stroke-dasharray="4 4"/>
       <text x="${W - pad}" y="${y(goal) - 4}" text-anchor="end">норма ${goal}</text>`
    : "";
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="График калорий">${goalLine}${bars}</svg>`;
}

function lineChart(points) {
  const W = 320, H = 140, pad = 22;
  const vals = points.map((p) => p.kg);
  const min = Math.min(...vals) - 1, max = Math.max(...vals) + 1;
  const x = (i) => (points.length === 1 ? W / 2 : pad + (i / (points.length - 1)) * (W - pad * 2));
  const y = (v) => H - pad - ((v - min) / (max - min)) * (H - pad * 2);
  const path = points.map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p.kg)}`).join(" ");
  const dots = points.map((p, i) => `<circle cx="${x(i)}" cy="${y(p.kg)}" r="3.5" fill="var(--accent)"/>`).join("");
  const first = points[0], last = points[points.length - 1];
  const fmt = (d) => d.slice(5).split("-").reverse().join(".");
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="График веса">
    <path d="${path}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linejoin="round"/>${dots}
    <text x="${x(0)}" y="${H - 4}" text-anchor="${points.length === 1 ? "middle" : "start"}">${fmt(first.date)}</text>
    ${points.length > 1 ? `<text x="${W - pad}" y="${H - 4}" text-anchor="end">${fmt(last.date)}</text>` : ""}
    <text x="${x(points.length - 1)}" y="${y(last.kg) - 10}" text-anchor="${points.length === 1 ? "middle" : "end"}">${last.kg} кг</text>
  </svg>`;
}

function renderStats() {
  const days = [...Array(7)].map((_, i) => shiftDate(todayKey(), i - 6));
  const vals = days.map((d) => round(totals(dayEntries(d)).kcal));
  const labels = days.map((d) => {
    const [y, m, dd] = d.split("-").map(Number);
    return new Date(y, m - 1, dd).toLocaleDateString("ru-RU", { weekday: "short" });
  });
  $("#week-chart").innerHTML = barChart(vals, labels, state.targets.kcal);
  const logged = vals.filter(Boolean);
  $("#avg-kcal").textContent = logged.length ? `в среднем ${round(logged.reduce((a, b) => a + b, 0) / logged.length)} ккал` : "";

  const w = state.weights.slice(-30);
  if (w.length) {
    $("#weight-chart").innerHTML = lineChart(w);
    const d = round(w[w.length - 1].kg - w[0].kg, 1);
    $("#weight-delta").textContent = w.length > 1 ? `${d > 0 ? "+" : ""}${d} кг` : "";
  } else {
    $("#weight-chart").innerHTML = `<p class="muted small">Записывайте вес, чтобы видеть динамику.</p>`;
    $("#weight-delta").textContent = "";
  }

  renderBodyHistory();

  let streak = 0;
  for (let d = todayKey(); dayEntries(d).length; d = shiftDate(d, -1)) streak++;
  if (!streak) for (let d = shiftDate(todayKey(), -1); dayEntries(d).length; d = shiftDate(d, -1)) streak++;
  $("#streak").textContent = streak;
}

function renderBodyHistory() {
  const ms = state.measurements;
  const box = $("#body-history");
  if (!ms.length) {
    box.innerHTML = `<p class="muted small">Внесите замеры в профиле и нажмите «Применить» — здесь появится динамика талии, бёдер и % жира.</p>`;
    $("#body-since").textContent = "";
    return;
  }
  const rows = [["waist", "Талия", "см"], ["hips", "Бёдра", "см"], ["neck", "Шея", "см"], ["bf", "% жира", "%"]];
  box.innerHTML = rows
    .map(([k, label, unit]) => {
      const vals = ms.filter((m) => m[k] != null);
      if (!vals.length) return "";
      const last = vals[vals.length - 1][k];
      const diff = round(last - vals[0][k], 1);
      const diffText = vals.length > 1 && diff ? ` <span class="muted">(${diff > 0 ? "+" : ""}${diff})</span>` : "";
      return `<div class="body-row"><span>${label}</span><span class="d">${last} ${unit}${diffText}</span></div>`;
    })
    .join("");
  $("#body-since").textContent = ms.length > 1 ? `изменение с ${fmtDate(ms[0].date)}` : `замер от ${fmtDate(ms[0].date)}`;
}

$("#weight-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const kg = round(Number($("#weight-input").value), 1);
  if (!(kg > 0)) return;
  const date = todayKey();
  state.weights = [...state.weights.filter((x) => x.date !== date), { date, kg }].sort((a, b) => a.date.localeCompare(b.date));
  state.profile.weight = kg;
  save();
  $("#weight-input").value = "";
  renderStats();
  toast("Вес записан");
});

// ---------- Старт ----------
renderToday();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
