const STORAGE_KEY = "lotto_recommender_history_v1";
const HISTORY_LIMIT = 12;
const DEFAULT_SET_COUNT = 5;
const FIRST_RUN_KEY = "lotto_recommender_first_run_v1";

function clampNumber(value, min, max, fallback) {
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  return Math.min(max, Math.max(min, Math.trunc(n)));
}

function randomIntInclusive(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function generateLottoSetWithBonus() {
  const picked = new Set();
  while (picked.size < 7) {
    picked.add(randomIntInclusive(1, 45));
  }
  const all = Array.from(picked).sort((a, b) => a - b);
  return {
    main: all.slice(0, 6),
    bonus: all[6],
  };
}

function formatSetNumbers(nums) {
  return nums.join(", ");
}

function normalizeSet(raw) {
  // New format: { main: number[6], bonus: number }
  if (raw && typeof raw === "object" && !Array.isArray(raw)) {
    const mainOk =
      Array.isArray(raw.main) &&
      raw.main.length === 6 &&
      raw.main.every((n) => Number.isInteger(n) && n >= 1 && n <= 45);
    const bonusOk = Number.isInteger(raw.bonus) && raw.bonus >= 1 && raw.bonus <= 45;
    if (mainOk && bonusOk && !raw.main.includes(raw.bonus)) {
      return { main: [...raw.main].sort((a, b) => a - b), bonus: raw.bonus };
    }
    return null;
  }

  // Old/alternate format: [numbers...]
  if (Array.isArray(raw)) {
    const nums = raw.filter((n) => Number.isInteger(n) && n >= 1 && n <= 45);
    const uniq = Array.from(new Set(nums)).sort((a, b) => a - b);
    if (uniq.length >= 7) {
      const main = uniq.slice(0, 6);
      const bonus = uniq.find((n) => !main.includes(n));
      if (bonus != null) return { main, bonus };
    }
    if (uniq.length === 6) {
      // No bonus stored in old history; keep main and mark bonus as missing.
      return { main: uniq, bonus: null };
    }
    return null;
  }

  return null;
}

function formatSetWithBonus(set) {
  const normalized = normalizeSet(set);
  if (!normalized) return "잘못된 기록";
  const bonusText = Number.isInteger(normalized.bonus) ? String(normalized.bonus) : "-";
  return `${formatSetNumbers(normalized.main)} + 보너스 ${bonusText}`;
}

function nowKoreanTimestamp() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${day} ${hh}:${mm}`;
}

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((x) => {
        if (!x || typeof x.at !== "string" || !Array.isArray(x.sets)) return null;
        const sets = x.sets.map(normalizeSet).filter(Boolean);
        if (sets.length === 0) return null;
        return { at: x.at, sets };
      })
      .filter(Boolean)
      .slice(0, HISTORY_LIMIT);
  } catch {
    return [];
  }
}

function saveHistory(history) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(0, HISTORY_LIMIT)));
}

function ballClassByNumber(n) {
  // Simple color grouping similar to common lotto visuals
  if (n <= 10) return "b1";
  if (n <= 20) return "b2";
  if (n <= 30) return "b3";
  if (n <= 40) return "b4";
  return "b5";
}

function renderSets(container, sets) {
  container.innerHTML = "";

  sets.forEach((set, idx) => {
    const normalized = normalizeSet(set);
    if (!normalized) return;
    const setEl = document.createElement("div");
    setEl.className = "set";

    const balls = document.createElement("div");
    balls.className = "balls";

    normalized.main.forEach((n) => {
      const b = document.createElement("span");
      b.className = `ball ${ballClassByNumber(n)}`;
      b.textContent = String(n);
      balls.appendChild(b);
    });

    const sep = document.createElement("span");
    sep.className = "separator";
    sep.textContent = "+";
    balls.appendChild(sep);

    const bonusLabel = document.createElement("span");
    bonusLabel.className = "bonus-label";
    bonusLabel.textContent = "B";
    balls.appendChild(bonusLabel);

    const bonusBall = document.createElement("span");
    bonusBall.className = "ball bonus";
    bonusBall.textContent = Number.isInteger(normalized.bonus) ? String(normalized.bonus) : "-";
    balls.appendChild(bonusBall);

    const meta = document.createElement("div");
    meta.className = "meta";

    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = `${idx + 1}세트`;

    meta.appendChild(chip);

    setEl.appendChild(balls);
    setEl.appendChild(meta);
    container.appendChild(setEl);
  });
}

function renderHistory(listEl, history) {
  listEl.innerHTML = "";
  if (history.length === 0) {
    const li = document.createElement("li");
    li.className = "muted";
    li.textContent = "아직 기록이 없어요. '추천받기'를 눌러보세요.";
    listEl.appendChild(li);
    return;
  }

  history.forEach((item) => {
    const li = document.createElement("li");
    const setsText = item.sets
      .map((s, i) => `${i + 1}세트: ${formatSetWithBonus(s)}`)
      .join(" / ");
    li.textContent = `${item.at} · ${setsText}`;
    listEl.appendChild(li);
  });
}

function setsToClipboardText(sets) {
  return sets.map((s, i) => `${i + 1}세트: ${formatSetWithBonus(s)}`).join("\n");
}

async function copyToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  // Fallback
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.left = "-9999px";
  document.body.appendChild(ta);
  ta.select();
  document.execCommand("copy");
  ta.remove();
}

function createToast() {
  const toast = document.getElementById("toast");
  const titleEl = document.getElementById("toastTitle");
  const msgEl = document.getElementById("toastMsg");
  const closeBtn = document.getElementById("toastClose");

  let timer = null;

  function hide() {
    if (timer) window.clearTimeout(timer);
    timer = null;
    toast.hidden = true;
  }

  function show(title, msg, timeoutMs = 2400) {
    titleEl.textContent = title;
    msgEl.textContent = msg;
    toast.hidden = false;
    if (timer) window.clearTimeout(timer);
    timer = window.setTimeout(hide, timeoutMs);
  }

  closeBtn.addEventListener("click", hide);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hide();
  });

  return { show, hide };
}

function main() {
  const btnGenerate = document.getElementById("btnGenerate");
  const btnCopy = document.getElementById("btnCopy");
  const btnClear = document.getElementById("btnClear");
  const resultSets = document.getElementById("resultSets");
  const historyList = document.getElementById("historyList");
  const status = document.getElementById("status");
  const toast = createToast();

  let lastSets = [];
  let history = loadHistory();
  renderHistory(historyList, history);

  function setStatus(msg) {
    status.textContent = msg || "";
  }

  function generate() {
    const setCount = clampNumber(DEFAULT_SET_COUNT, 1, 10, 5);
    lastSets = Array.from({ length: setCount }, () => generateLottoSetWithBonus());
    renderSets(resultSets, lastSets);

    btnCopy.disabled = lastSets.length === 0;
    setStatus(`생성 완료: ${setCount}세트`);
    toast.show("추천 완료", "5세트(보너스 포함) 번호를 생성했어요.");

    history = [{ at: nowKoreanTimestamp(), sets: lastSets }, ...history].slice(0, HISTORY_LIMIT);
    saveHistory(history);
    renderHistory(historyList, history);
  }

  btnGenerate.addEventListener("click", generate);

  btnCopy.addEventListener("click", async () => {
    if (lastSets.length === 0) return;
    try {
      await copyToClipboard(setsToClipboardText(lastSets));
      setStatus("클립보드에 복사했어요.");
      toast.show("복사 완료", "클립보드에 결과를 복사했어요.");
    } catch {
      setStatus("복사에 실패했어요. 브라우저 권한을 확인해주세요.");
      toast.show("복사 실패", "브라우저 권한을 확인해주세요.", 3200);
    }
  });

  btnClear.addEventListener("click", () => {
    localStorage.removeItem(STORAGE_KEY);
    history = [];
    renderHistory(historyList, history);
    setStatus("기록을 삭제했어요.");
    toast.show("기록 삭제", "저장된 최근 추천 기록을 삭제했어요.");
  });

  // Keyboard shortcuts
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      generate();
      return;
    }
    if ((e.ctrlKey || e.metaKey) && (e.key === "c" || e.key === "C")) {
      if (lastSets.length === 0) return;
      // Let browser native copy happen if user is selecting text
      const sel = window.getSelection?.();
      if (sel && String(sel).trim().length > 0) return;
      e.preventDefault();
      btnCopy.click();
    }
  });

  // First run: auto-generate once for better UX
  try {
    const firstRun = localStorage.getItem(FIRST_RUN_KEY);
    if (!firstRun) {
      localStorage.setItem(FIRST_RUN_KEY, "1");
      generate();
    }
  } catch {
    // ignore
  }
}

document.addEventListener("DOMContentLoaded", main);

