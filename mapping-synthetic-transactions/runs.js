// ===== Medianville runs: which day a viewer opens, and the picker that changes it =====
// Reads data/runs/manifest.json (written by tools/pack_runs.py): every published run with its id, date, label, path,
// size and record count. A page opens the manifest's default run, or the one named by ?run=<id>. Choosing another day
// in the picker reloads the page with ?run= set, keeping the hash, so each day is its own link. If the manifest can't
// be read, the page falls back to the zip it was built with.
(function () {
  const SHORT = {
    baseline: 'baseline', holiday_major: 'holiday', holiday_minor: 'minor holiday', saturday: 'Saturday', sunday: 'Sunday',
    eitc_wave: 'tax refunds land', ssi_first: 'SSI day', ss_third: 'Social Security, 3rd', ss_wednesday: 'Social Security Wednesday',
    friday: 'Friday payday', tax_season_weekday: 'tax season', weekday_early: 'early month', weekday_mid: 'mid-month',
    weekday_late: 'late month', storm: 'winter storm', heat: 'heat wave',
  };
  const dateLabel = (iso, opts) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || ''); if (!m) return iso || '';
    return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])).toLocaleDateString('en-US', Object.assign({ timeZone: 'UTC' }, opts));
  };
  // 'Wed, Mar 3 · baseline'
  const optionLabel = (r) => dateLabel(r.date, { weekday: 'short', month: 'short', day: 'numeric' }) + ' · ' + (SHORT[r.class] || r.class);

  // bases: where the project root is from this page, tried in order ('' for the root page, '../' for a subfolder)
  async function resolve(bases) {
    const want = new URLSearchParams(location.search).get('run');
    for (const base of bases) {
      let man = null;
      try { const res = await fetch(base + 'data/runs/manifest.json', { cache: 'no-cache' }); if (res.ok) man = await res.json(); } catch (e) { /* try the next place */ }
      if (!man || !Array.isArray(man.runs) || !man.runs.length) continue;
      const run = man.runs.find((r) => r.id === want) || man.runs.find((r) => r.id === man.default) || man.runs[man.runs.length - 1];
      return { base, manifest: man, run, url: base + run.path, asked: want, found: !want || run.id === want };
    }
    return null;
  }

  // fills a <select> with the runs, newest version first, and reloads on change
  function picker(select, sel) {
    if (!select || !sel || select.dataset.ready) return;
    select.dataset.ready = '1';
    const groups = {};
    for (const r of sel.manifest.runs) (groups[r.version] = groups[r.version] || []).push(r);
    const doc = select.ownerDocument;
    select.textContent = '';
    for (const v of Object.keys(groups).sort().reverse()) {
      const g = doc.createElement('optgroup');
      g.label = v === 'v1' ? 'v1 (the first version)' : v + ' · a year in typical days';
      const rows = groups[v].slice().sort((a, b) => (a.class === 'baseline' ? -1 : b.class === 'baseline' ? 1 : a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
      for (const r of rows) {
        const o = doc.createElement('option');
        o.value = r.id; o.textContent = optionLabel(r);
        o.title = r.label + ' · ' + (r.records || 0).toLocaleString('en-US') + ' records';
        if (r.id === sel.run.id) o.selected = true;
        g.appendChild(o);
      }
      select.appendChild(g);
    }
    select.hidden = false;
    select.addEventListener('change', () => {
      const u = new URL(location.href);
      if (select.value === sel.manifest.default) u.searchParams.delete('run'); else u.searchParams.set('run', select.value);
      location.assign(u.toString());
    });
  }

  // keeps ?run= on links to the other viewer
  function carry(a, sel) {
    if (!a || !sel || sel.run.id === sel.manifest.default) return;
    try { const u = new URL(a.getAttribute('href'), location.href); u.searchParams.set('run', sel.run.id); a.href = u.toString(); } catch (e) { /* leave the link */ }
  }

  window.MedianvilleRuns = { resolve, picker, carry, dateLabel, optionLabel };
})();
