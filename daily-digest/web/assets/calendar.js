/* ============================================================
   calendar.js — pure client-side month calendar over window.DIGESTS
   Shared by the viewer overlay (index.html) and the full calendar page.
   No backend, no fetch — manifest.js defines window.DIGESTS.
   ============================================================ */
(function (global) {
  const WD = ["日", "一", "二", "三", "四", "五", "六"];
  const MO = ["1 月", "2 月", "3 月", "4 月", "5 月", "6 月",
              "7 月", "8 月", "9 月", "10 月", "11 月", "12 月"];

  function byDate() {
    const map = {};
    (global.DIGESTS || []).forEach(d => { map[d.date] = d; });
    return map;
  }

  function latestDate() {
    const ds = (global.DIGESTS || []).map(d => d.date).sort();
    return ds[ds.length - 1] || null;
  }

  function pad(n) { return String(n).padStart(2, "0"); }
  function ymd(y, m, d) { return `${y}-${pad(m + 1)}-${pad(d)}`; }

  /**
   * Render a month grid into `el`.
   * opts = { year, month(0-11), selected, onPick(date), onMonth(y,m) }
   * Returns nothing; re-call to repaint.
   */
  function renderCalendar(el, opts) {
    const map = byDate();
    const y = opts.year, m = opts.month;
    const first = new Date(Date.UTC(y, m, 1));
    const startDow = first.getUTCDay();
    const days = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();

    let h = '<div class="cal-head">';
    h += `<button class="cal-nav" data-go="-1" aria-label="上个月">‹</button>`;
    h += `<div class="cal-title">${y} 年 ${MO[m]}</div>`;
    h += `<button class="cal-nav" data-go="1" aria-label="下个月">›</button>`;
    h += '</div>';
    h += '<div class="cal-grid">';
    WD.forEach(w => { h += `<div class="cal-dow">${w}</div>`; });
    for (let i = 0; i < startDow; i++) h += '<div class="cal-cell empty"></div>';
    for (let d = 1; d <= days; d++) {
      const date = ymd(y, m, d);
      const has = !!map[date];
      const sel = date === opts.selected;
      const cls = ["cal-cell", has ? "has" : "no", sel ? "sel" : ""].join(" ").trim();
      const title = has ? (map[date].title || "查看日报").replace(/"/g, "&quot;") : "";
      h += `<div class="${cls}" ${has ? `data-date="${date}" title="${title}"` : ""}>`
         + `<span class="d">${d}</span>${has ? '<span class="mark"></span>' : ''}</div>`;
    }
    h += '</div>';
    el.innerHTML = h;

    el.querySelectorAll(".cal-nav").forEach(b => b.addEventListener("click", () => {
      const go = parseInt(b.dataset.go, 10);
      let nm = m + go, ny = y;
      if (nm < 0) { nm = 11; ny--; }
      if (nm > 11) { nm = 0; ny++; }
      if (opts.onMonth) opts.onMonth(ny, nm);
    }));
    el.querySelectorAll(".cal-cell.has").forEach(c => c.addEventListener("click", () => {
      if (opts.onPick) opts.onPick(c.dataset.date);
    }));
  }

  global.Digest = { renderCalendar, byDate, latestDate, MO, WD,
                    parseMonth: d => { const [y, m] = d.split("-"); return [+y, +m - 1]; } };
}(window));
