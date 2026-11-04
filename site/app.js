(() => {
  "use strict";
  const BINS = [5, 10, 20, 30, 45];  // index thresholds → 6 classes
  const RAMP = ["--r1", "--r2", "--r3", "--r4", "--r5", "--r6"];
  const LOCATION = {
    "4chan": "Post's country flag", reddit: "Country subreddit", gdelt: "Outlet's country",
    google_news: "Country edition", mastodon: "Instance country", hackernews: "None (global only)",
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
    paint();
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
    paths.each(function (d) {
      const c = byNum.get(String(d.id).padStart(3, "0"));
      const s = stat(c);
      const has = s && s.confidence !== "insufficient" && s.index != null;
      this.classList.toggle("nodata", !has);
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
       <span class="ramp"><span class="nd"></span>&nbsp;Not enough data</span>`;
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

  function render() { paint(); rankTable(); globalPanel(); status(); }

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
