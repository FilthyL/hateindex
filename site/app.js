(() => {
  "use strict";
  const BINS = [5, 10, 20, 30, 45];  // index thresholds → 6 classes
  const RAMP = ["--r1", "--r2", "--r3", "--r4", "--r5", "--r6"];
  const LOCATION = {
    "4chan": "Post's country flag", reddit: "Country subreddit", gdelt: "Outlet's country",
    google_news: "Country edition", mastodon: "Instance country", lemmy: "Instance country", hackernews: "None (global only)",
    bluesky: "None (global only)", medium: "None (global only)", wordpress: "None (global only)",
    youtube: "Needs API key", x: "Needs API key",
  };
  let data = null, layer = "people", byNum = new Map(), paths = null;
  const tip = document.getElementById("tip");
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const pct = (x) => `${Math.round(100 * x)}%`;

  // ---------- theme ----------
  const themeBtn = document.getElementById("theme");
  try { const t = localStorage.getItem("theme"); if (t) document.documentElement.dataset.theme = t; } catch (e) {}
  themeBtn.onclick = () => {
    const dark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("theme", document.documentElement.dataset.theme); } catch (e) {}
    if (data) render(); else paint();
  };

  const bin = (v) => { let i = 0; while (i < BINS.length && v >= BINS[i]) i++; return i; };
  const stat = (c) => c && c.layers && c.layers[layer];
  const ranked = (c) => { const s = stat(c); return s && !c.domestic && s.confidence !== "insufficient" && s.index != null; };

  // ---------- map ----------
  async function drawMap() {
    const world = await d3.json("vendor/countries-50m.json");
    const countries = topojson.feature(world, world.objects.countries).features.filter((f) => f.id !== "010");
    const el = document.getElementById("map");
    const W = 1000, H = 500;
    const projection = d3.geoNaturalEarth1().fitExtent([[6, 6], [W - 6, H - 6]], { type: "Sphere" });
    const path = d3.geoPath(projection);
    const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img");
    const defs = svg.append("defs");
    const pat = defs.append("pattern").attr("id", "hatch").attr("patternUnits", "userSpaceOnUse")
      .attr("width", 5).attr("height", 5).attr("patternTransform", "rotate(45)");
    pat.append("rect").attr("width", 5).attr("height", 5).attr("class", "hatch-bg");
    pat.append("line").attr("x1", 0).attr("y1", 0).attr("x2", 0).attr("y2", 5).attr("class", "hatch-ln").attr("stroke-width", 1.4);
    // "some data, not enough to score": dots, so it reads differently from "no data"
    const dots = defs.append("pattern").attr("id", "dots").attr("patternUnits", "userSpaceOnUse").attr("width", 4).attr("height", 4);
    dots.append("rect").attr("width", 4).attr("height", 4).attr("class", "hatch-bg");
    dots.append("circle").attr("cx", 2).attr("cy", 2).attr("r", 0.9).attr("class", "dot");
    const g = svg.append("g");
    g.append("path").datum({ type: "Sphere" }).attr("class", "sphere").attr("d", path);
    paths = g.selectAll("path.country").data(countries).join("path").attr("class", "country").attr("d", path)
      .on("mousemove", (ev, d) => show(ev, d))
      .on("mouseleave", hide)
      .on("click", (ev, d) => { ev.stopPropagation(); show(ev, d, true); });
    svg.on("click", hide);
    svg.call(d3.zoom().scaleExtent([1, 8]).translateExtent([[0, 0], [W, H]])
      .on("zoom", (ev) => { g.attr("transform", ev.transform); hide(); }));
    paint();
  }

  function paint() {
    if (!paths) return;
    d3.select(".hatch-bg").attr("fill", css("--nodata"));
    d3.select(".hatch-ln").attr("stroke", css("--surface"));
    d3.selectAll(".hatch-bg").attr("fill", css("--nodata"));
    d3.selectAll(".dot").attr("fill", css("--r4"));
    paths.each(function (d) {
      const c = byNum.get(String(d.id).padStart(3, "0"));
      const s = stat(c);
      const has = s && s.confidence !== "insufficient" && s.index != null;
      const thin = !has && s && s.authors > 0;
      this.classList.toggle("nodata", !has && !thin);
      this.classList.toggle("thin", thin);
      this.style.fill = has ? css(RAMP[bin(s.index)]) : "";
      this.setAttribute("aria-label", `${c ? c.name : d.properties.name}: ${has ? s.index.toFixed(1) : "no data"}`);
    });
    legend();
  }

  function legend() {
    const ticks = ["0", ...BINS.map(String)];
    document.getElementById("legend").innerHTML =
      `<span>Hate index</span>
       <div><div class="ramp">${RAMP.map((v) => `<span class="sw" style="background:${css(v)}"></span>`).join("")}</div>
       <div class="ticks">${ticks.map((t, i) => `<span>${i === ticks.length - 1 ? t + "+" : t}</span>`).join("")}</div></div>
       <span class="ramp"><span class="nd thin-sw"></span>&nbsp;Some data (under 10 people)</span>
       <span class="ramp"><span class="nd"></span>&nbsp;No data yet</span>`;
  }

  // ---------- tooltip ----------
  function bars(items) {
    if (!items || !items.length) return `<div class="empty">—</div>`;
    return items.slice(0, 4).map((r) => `<div class="bar"><span class="t">${esc(r.label)}</span>
      <span class="v">${pct(r.share)}</span><div class="track"><div class="fill" style="width:${Math.max(3, 100 * r.share)}%"></div></div></div>`).join("");
  }

  function tipHTML(name, c) {
    const s = stat(c);
    if (!s || s.confidence === "insufficient") {
      return `<h4>${esc(name)}</h4><p>${s ? `Only ${s.authors} author${s.authors === 1 ? "" : "s"} so far, below the 10 needed to score.` : "No posts about Indians collected from here yet."}</p>`;
    }
    const total = data.countries ? Object.values(data.countries).filter(ranked).length : 0;
    return `<div class="row"><h4>${esc(c.name)}</h4><span class="badge">${esc(s.confidence)} confidence</span></div>
      <div class="row"><span class="big">${s.index.toFixed(1)}</span>
        <span class="sub">${c.domestic ? "domestic, not ranked" : `rank ${s.rank} of ${total}`}<br>${s.authors.toLocaleString()} people · ${s.posts.toLocaleString()} posts</span></div>
      <p>${esc(c.summary[layer])}</p>
      <div class="lbl">Why: main reasons for hostility</div>${bars(s.reasons)}
      <div class="lbl">What: stereotypes repeated</div>${bars(s.stereotypes)}
      <div class="sub" style="margin-top:8px">${pct(s.hateful_author_share)} of authors hostile · ${s.slur_posts} posts with slurs · ${pct(c.sarcasm_share || 0)} excluded as sarcasm</div>`;
  }

  function show(ev, d, pinned) {
    const c = byNum.get(String(d.id).padStart(3, "0"));
    tip.innerHTML = tipHTML(c ? c.name : d.properties.name, c);
    tip.hidden = false;
    paths.classed("hot", (x) => x === d);
    const pad = 14, r = tip.getBoundingClientRect();
    let x = ev.clientX + pad, y = ev.clientY + pad;
    if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - pad;
    if (y + r.height > innerHeight - 8) y = innerHeight - r.height - 8;
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = Math.max(8, y) + "px";
  }
  function hide() { tip.hidden = true; paths && paths.classed("hot", false); }

  // ---------- tables ----------
  function rankTable() {
    const rows = Object.values(data.countries || {}).filter(ranked).sort((a, b) => stat(a).rank - stat(b).rank);
    const tb = document.querySelector("#rank tbody");
    tb.innerHTML = rows.length ? rows.map((c) => { const s = stat(c); return `<tr data-num="${c.num}">
        <td>${s.rank}</td><td>${esc(c.name)}</td><td class="num">${s.index.toFixed(1)}</td><td class="num">${s.authors.toLocaleString()}</td>
        <td>${esc(s.reasons[0] ? s.reasons[0].label : "—")}</td><td>${esc(s.confidence)}</td></tr>`; }).join("")
      : `<tr><td colspan="6" class="empty">No country has enough data for this measure yet.</td></tr>`;
    tb.querySelectorAll("tr[data-num]").forEach((tr) => tr.addEventListener("click", (ev) => {
      const f = paths && paths.data().find((d) => String(d.id).padStart(3, "0") === tr.dataset.num);
      if (f) { ev.stopPropagation(); show(ev, f, true); }
    }));
  }

  function globalPanel() {
    const s = data.global && data.global[layer];
    const t = data.totals || {};
    const el = document.getElementById("global");
    if (!s || !s.authors) { el.innerHTML = `<p class="empty">No posts collected yet.</p>`; return; }
    el.innerHTML = `<div class="row" style="display:flex;gap:24px;flex-wrap:wrap">
        <div><div class="tip-big" style="font-size:30px;font-weight:700">${s.raw.toFixed(1)}</div><div class="muted small">global index</div></div>
        <div><div style="font-size:30px;font-weight:700">${pct(s.hateful_author_share)}</div><div class="muted small">of authors posted something hostile</div></div></div>
      <p class="muted small">${(t.targeted || 0).toLocaleString()} posts about Indians, out of ${(t.posts || 0).toLocaleString()} collected. ${(t.sarcasm_excluded || 0).toLocaleString()} removed as sarcasm, ${(t.counter_speech || 0).toLocaleString()} counter-speech, ${(t.state_critique || 0).toLocaleString()} criticism of the Indian state (not counted).</p>
      <h3>Why: reasons worldwide</h3>${bars(s.reasons)}
      <h3>What: stereotypes worldwide</h3>${bars(s.stereotypes)}`;
  }

  function sourcesTable() {
    const src = data.sources || {};
    const names = Object.keys(LOCATION);
    document.querySelector("#sources-table tbody").innerHTML = names.map((n) => {
      const s = src[n] || {};
      const st = s.error ? `<span title="${esc(s.error)}">${String(s.error).startsWith("RuntimeError: skipped") ? "skipped" : "error"}</span>` : (s.last_run ? s.last_run.slice(0, 10) : "never");
      return `<tr><td>${esc(n)}</td><td>${esc(LOCATION[n])}</td><td class="num">${(s.stored ?? s.posts ?? 0).toLocaleString()}</td><td>${st}</td></tr>`;
    }).join("");
  }

  function status() {
    const el = document.getElementById("status");
    const n = Object.values(data.countries || {}).filter(ranked).length;
    if (!data.totals || !data.totals.posts) {
      el.innerHTML = "<strong>No data yet.</strong> The first collection run hasn’t finished. The map fills in after the scheduled GitHub Actions job runs.";
    } else {
      el.innerHTML = `Updated <strong>${esc(data.generated_at.slice(0, 16).replace("T", " "))} UTC</strong> · ${esc(data.window)} · ${n} ${n === 1 ? "country" : "countries"} with enough data for this measure.`;
    }
  }

  // ---------- world overview ----------
  const num = (x) => (x ?? 0).toLocaleString();

  function kpis() {
    const o = data.overview || {}, t = data.totals || {}, g = (data.global || {})[layer] || {};
    const scored = (o.countries_scored || {})[layer] || 0;
    document.getElementById("kpis").innerHTML = [
      [num(t.targeted), "posts about Indians (all sources)"],
      [num(g.authors), "people analysed"],
      [`${o.countries_with_data || 0}`, "countries with any data"],
      [`${scored}`, "countries with enough to score"],
      [g.authors ? pct(g.hateful_author_share) : "—", "of people posted something hostile"],
    ].map(([v, l]) => `<div class="kpi"><b>${v}</b><span>${l}</span></div>`).join("");
  }

  function regionsPanel() {
    const rs = (data.overview || {}).regions || [];
    const el = document.getElementById("regions");
    if (!rs.length) { el.innerHTML = `<p class="empty">No regional data yet.</p>`; return; }
    // scale to the next multiple of 10 above the highest region (min 20), and say so
    const max = Math.max(20, Math.ceil(Math.max(...rs.map((r) => r.index || 0)) / 10) * 10);
    document.getElementById("regions-scale").textContent = `Bar scale 0–${max}.`;
    el.innerHTML = rs.map((r) => {
      const ok = r.confidence !== "insufficient";
      return `<div class="hbar"><span>${esc(r.region)}</span>
        <div class="track"><div class="fill" style="width:${ok ? Math.max(1.5, 100 * r.index / max) : 0}%"></div></div>
        <span class="v">${ok ? r.index.toFixed(1) : "—"}</span>
        <span class="meta">${num(r.authors)} people · ${r.countries} countr${r.countries === 1 ? "y" : "ies"} · ${ok ? esc(r.confidence) + " confidence" : "not enough data"}${r.reasons[0] ? " · mostly " + esc(r.reasons[0].label.toLowerCase()) : ""}</span></div>`;
    }).join("");
  }

  function timelineChart() {
    const o = data.overview || {};
    const rows = ((o.timeline || {})[layer] || []).map((d) => ({ ...d, other: d.posts - d.hostile }));
    const el = document.getElementById("timeline");
    document.getElementById("tl-legend").innerHTML =
      `<span><span class="sw-h"></span>Hostile</span><span><span class="sw-o"></span>Other posts</span>`;
    if (!rows.length || !rows.some((d) => d.posts)) { el.innerHTML = `<p class="empty">No dated posts yet.</p>`; return; }
    const W = 520, H = 200, m = { t: 12, r: 8, b: 22, l: 34 };
    const x = d3.scaleBand().domain(rows.map((d) => d.week)).range([m.l, W - m.r]).paddingInner(0.15);
    const y = d3.scaleLinear().domain([0, d3.max(rows, (d) => d.posts) || 1]).nice().range([H - m.b, m.t]);
    el.innerHTML = "";
    const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("role", "img")
      .attr("aria-label", "Weekly posts about Indians, split into hostile and other");
    svg.append("g").attr("class", "axis").attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(4).tickSize(-(W - m.l - m.r)).tickFormat(d3.format("~s")))
      .call((g) => g.select(".domain").remove()).call((g) => g.selectAll("line").attr("stroke-opacity", 0.5));
    const months = rows.filter((d, i) => i === 0 || d.week.slice(5, 7) !== rows[i - 1].week.slice(5, 7));
    svg.append("g").attr("class", "axis").attr("transform", `translate(0,${H - m.b})`)
      .call(d3.axisBottom(x).tickValues(months.map((d) => d.week)).tickSize(0).tickPadding(6)
        .tickFormat((w) => new Date(w + "T00:00:00Z").toLocaleString("en", { month: "short", timeZone: "UTC" })))
      .call((g) => g.select(".domain").remove());
    const bars = svg.append("g");
    rows.forEach((d) => {
      const bx = x(d.week), bw = x.bandwidth();
      if (d.other) bars.append("rect").attr("x", bx).attr("width", bw).attr("y", y(d.other)).attr("height", y(0) - y(d.other))
        .attr("fill", css("--neutral")).attr("rx", d.hostile ? 0 : 2);
      if (d.hostile) bars.append("rect").attr("x", bx).attr("width", bw).attr("y", y(d.posts)).attr("height", Math.max(0, y(d.other) - y(d.posts) - (d.other ? 1 : 0)))
        .attr("fill", css("--r5")).attr("rx", 2);
      bars.append("rect").attr("x", bx).attr("width", bw).attr("y", m.t).attr("height", H - m.b - m.t).attr("fill", "transparent")
        .on("mousemove", (ev) => {
          tip.innerHTML = `<h4>Week of ${esc(d.week)}</h4><p>${num(d.posts)} posts about Indians · ${num(d.hostile)} hostile${d.posts ? ` (${pct(d.hostile / d.posts)})` : ""}</p>`;
          tip.hidden = false; tip.style.left = Math.min(ev.clientX + 14, innerWidth - 350) + "px"; tip.style.top = ev.clientY + 14 + "px";
        }).on("mouseleave", hide);
    });
    let note = "";
    if (o.collection_started) {
      const start = o.collection_started.slice(0, 10);
      const wk = rows.find((d) => d.week <= start && start < (rows[rows.indexOf(d) + 1] || { week: "9999" }).week);
      if (wk) {
        const cx = x(wk.week) + x.bandwidth() / 2;
        svg.append("line").attr("class", "mark-line").attr("x1", cx).attr("x2", cx).attr("y1", m.t).attr("y2", H - m.b);
        svg.append("text").attr("class", "mark-text").attr("x", cx - 4).attr("y", m.t + 8).attr("text-anchor", "end").text("collection started");
      }
      note = `Collection started ${start}. Earlier weeks only include older posts from sources that can be searched back in time (Hacker News, news, blogs), so they undercount — the jump at the start is the collector switching on, not a surge in hostility.`;
    }
    document.getElementById("tl-note").textContent = note;
  }

  function bySource() {
    const rows = (data.overview || {}).by_source || [];
    const el = document.getElementById("by-source");
    if (!rows.length) { el.innerHTML = `<p class="empty">—</p>`; return; }
    const max = Math.max(...rows.map((r) => r.about_indians));
    el.innerHTML = `<div class="legend small" style="margin:0 0 6px"><span><span class="sw-h"></span>Hostile</span><span><span class="sw-o"></span>Other posts</span></div>` +
      rows.map((r) => `<div class="hbar"><span>${esc(r.source)}</span>
        <div class="stack" style="width:${Math.max(2, 100 * r.about_indians / max)}%">
          ${r.hostile ? `<div class="h" style="flex:${r.hostile}"></div>` : ""}${r.about_indians - r.hostile ? `<div class="o" style="flex:${r.about_indians - r.hostile}"></div>` : ""}</div>
        <span class="v">${num(r.about_indians)}</span>
        <span class="meta">${num(r.hostile)} hostile (${pct(r.hostile / (r.about_indians || 1))})</span></div>`).join("");
  }

  function coverageTable() {
    const rows = Object.values(data.countries || {}).filter((c) => stat(c) && stat(c).authors)
      .sort((a, b) => stat(b).authors - stat(a).authors);
    const tb = document.querySelector("#coverage tbody");
    tb.innerHTML = rows.length ? rows.map((c) => {
      const s = stat(c), scored = s.confidence !== "insufficient";
      const st = c.domestic ? "domestic" : scored ? `${s.confidence} confidence` : `needs ${10 - s.authors} more`;
      return `<tr data-num="${c.num}"><td>${esc(c.name)}</td><td>${esc(c.region || "")}</td><td class="num">${num(s.authors)}</td>
        <td class="num">${scored ? s.index.toFixed(1) : "—"}</td><td><span class="status-pill">${esc(st)}</span></td></tr>`;
    }).join("") : `<tr><td colspan="5" class="empty">No country data for this measure yet.</td></tr>`;
    tb.querySelectorAll("tr[data-num]").forEach((tr) => tr.addEventListener("click", (ev) => {
      const f = paths && paths.data().find((d) => String(d.id).padStart(3, "0") === tr.dataset.num);
      if (f) { ev.stopPropagation(); show(ev, f, true); }
    }));
  }

  function render() { paint(); kpis(); regionsPanel(); timelineChart(); bySource(); coverageTable(); rankTable(); globalPanel(); status(); }

  document.querySelectorAll(".seg").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".seg").forEach((x) => x.classList.toggle("active", x === b));
    layer = b.dataset.layer; hide(); render();
  }));
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", paint);
  addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });

  fetch("data/index.json", { cache: "no-cache" }).then((r) => (r.ok ? r.json() : {})).catch(() => ({}))
    .then((d) => {
      data = d || {};
      Object.values(data.countries || {}).forEach((c) => c.num && byNum.set(String(c.num).padStart(3, "0"), c));
      drawMap().then(render);
      sourcesTable();
    });
})();
