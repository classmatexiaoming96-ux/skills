/* ============================================================
   viewer.js — index.html shell: default to latest digest, navigate
   prev/next, open a calendar overlay to jump to any historical date.
   State lives in location.hash (#YYYY-MM-DD).
   ============================================================ */
(function () {
  const D = window.Digest;
  const frame   = document.getElementById("frame");
  const titleEl = document.getElementById("vTitle");
  const subEl   = document.getElementById("vSub");
  const prevBtn = document.getElementById("vPrev");
  const nextBtn = document.getElementById("vNext");
  const calBtn  = document.getElementById("vCal");
  const overlay = document.getElementById("calOverlay");
  const calBox  = document.getElementById("calBox");
  const closeBtn= document.getElementById("calClose");

  const dates = (window.DIGESTS || []).map(d => d.date).sort(); // ascending
  const meta  = D.byDate();

  function isValid(d) { return dates.includes(d); }
  function current() {
    const h = (location.hash || "").replace(/^#/, "");
    return isValid(h) ? h : (dates[dates.length - 1] || null);
  }
  function neighbour(date, dir) {
    const i = dates.indexOf(date);
    const j = i + dir;
    return (j >= 0 && j < dates.length) ? dates[j] : null;
  }

  function show(date) {
    if (!date) {
      titleEl.textContent = "暂无日报";
      subEl.textContent = "运行 daily-digest skill 生成第一期";
      return;
    }
    frame.src = date + ".html";
    const m = meta[date] || {};
    titleEl.textContent = date;
    const bits = [];
    if (m.weekday) bits.push(m.weekday);
    if (m.edition) bits.push("第 " + m.edition + " 期");
    if (date === dates[dates.length - 1]) bits.push("最新");
    subEl.textContent = bits.join(" · ");
    prevBtn.disabled = !neighbour(date, -1);
    nextBtn.disabled = !neighbour(date, +1);
    document.title = "AI 每日速递 · " + date;
  }

  function go(date) {
    if (!date) return;
    if (("#" + date) !== location.hash) location.hash = date;
    else show(date);
  }

  prevBtn.addEventListener("click", () => go(neighbour(current(), -1)));
  nextBtn.addEventListener("click", () => go(neighbour(current(), +1)));
  window.addEventListener("hashchange", () => { show(current()); });

  // ---- calendar overlay ----
  let calY, calM;
  function paintCal() {
    D.renderCalendar(calBox, {
      year: calY, month: calM, selected: current(),
      onMonth: (y, m) => { calY = y; calM = m; paintCal(); },
      onPick: (date) => { closeCal(); go(date); },
    });
  }
  function openCal() {
    const cur = current() || dates[dates.length - 1];
    if (cur) { const [y, m] = D.parseMonth(cur); calY = y; calM = m; }
    else { const now = new Date(); calY = now.getFullYear(); calM = now.getMonth(); }
    paintCal();
    overlay.classList.add("open");
  }
  function closeCal() { overlay.classList.remove("open"); }
  calBtn.addEventListener("click", openCal);
  closeBtn.addEventListener("click", closeCal);
  overlay.addEventListener("click", e => { if (e.target === overlay) closeCal(); });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") closeCal();
    if (overlay.classList.contains("open")) return;
    if (e.key === "ArrowLeft")  go(neighbour(current(), -1));
    if (e.key === "ArrowRight") go(neighbour(current(), +1));
  });

  // init
  show(current());
}());
