<script lang="ts">
  import Dialect from "../data/Dialect";
  import type Implementation from "../data/Implementation";
  import sortVersions from "../data/sortVersions";
  import Spinner from "./Spinner.svelte";

  let { implementation }: { implementation: Implementation } = $props();

  interface Point {
    version: string;
    total: number;
    failed: number;
    errored: number;
    skipped: number;
  }

  const dialects = Dialect.newestToOldest();
  let selected = $state(Dialect.latest());
  let loading = $state(true);
  let points = $state<Point[]>([]);

  $effect(() => {
    const dialect = selected;
    let cancelled = false;
    loading = true;
    void (async () => {
      try {
        const reports = await implementation.fetchVersionedReportsFor(dialect);
        if (cancelled) return;
        points = [...reports.entries()]
          .sort(([a], [b]) => sortVersions(a, b))
          .map(([version, data]) => {
            const totals = data.implementationsResults.values().next().value!
              .totals;
            const failed = totals.failedTests ?? 0;
            const errored = totals.erroredTests ?? 0;
            const skipped = totals.skippedTests ?? 0;
            return {
              version: `v${version}`,
              total: failed + errored + skipped,
              failed,
              errored,
              skipped,
            };
          });
      } catch {
        if (!cancelled) points = [];
      } finally {
        if (!cancelled) loading = false;
      }
    })();
    return () => {
      cancelled = true;
    };
  });

  function onDialect(e: Event) {
    selected = Dialect.withName((e.target as HTMLSelectElement).value);
  }

  // chart geometry (viewBox units; SVG scales responsively)
  const W = 760;
  const H = 320;
  const PAD = { t: 18, r: 20, b: 52, l: 46 };
  const innerW = W - PAD.l - PAD.r;
  const innerH = H - PAD.t - PAD.b;

  const maxY = $derived(Math.max(1, ...points.map((p) => p.total)));
  const xOf = (i: number) =>
    points.length <= 1
      ? PAD.l + innerW / 2
      : PAD.l + (i / (points.length - 1)) * innerW;
  const yOf = (v: number) => PAD.t + innerH - (v / maxY) * innerH;
  const line = $derived(
    points.map((p, i) => `${i ? "L" : "M"}${xOf(i)},${yOf(p.total)}`).join(" "),
  );
  const ticks = $derived(
    Array.from({ length: 3 }, (_, i) => Math.round((maxY / 2) * i)),
  );
</script>

<div class="card">
  <header class="vt-head">
    <span>Versions trend</span>
    <select class="vt-select mono" value={selected.shortName} onchange={onDialect} aria-label="Dialect for versions trend">
      {#each dialects as d (d.shortName)}
        <option value={d.shortName}>{d.prettyName}</option>
      {/each}
    </select>
  </header>
  <div class="body">
    {#if loading}
      <Spinner />
    {:else if points.length === 0}
      <div class="empty-note">
        No {selected.prettyName} results across versions of {implementation.id}.
      </div>
    {:else}
      <svg class="vt-chart" viewBox="0 0 {W} {H}" role="img" aria-label="Unsuccessful tests across versions">
        {#each ticks as t (t)}
          <line class="vt-grid" x1={PAD.l} y1={yOf(t)} x2={W - PAD.r} y2={yOf(t)} />
          <text class="vt-axis" x={PAD.l - 8} y={yOf(t) + 4} text-anchor="end">{t}</text>
        {/each}
        <path class="vt-line" d={line} />
        {#each points as p, i (p.version)}
          <circle class="vt-dot" cx={xOf(i)} cy={yOf(p.total)} r="4">
            <title>{p.version}: {p.total} unsuccessful ({p.failed} failed, {p.errored} errored, {p.skipped} skipped)</title>
          </circle>
          <text
            class="vt-axis"
            x={xOf(i)}
            y={H - PAD.b + 18}
            text-anchor="end"
            transform="rotate(-35 {xOf(i)} {H - PAD.b + 18})"
          >{p.version}</text>
        {/each}
      </svg>
    {/if}
  </div>
</div>

<style>
  .vt-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .vt-select {
    border: 1px solid var(--border-strong);
    border-radius: 7px;
    background: var(--surface);
    color: var(--text);
    font-size: 12px;
    padding: 4px 8px;
    cursor: pointer;
  }
  .vt-chart {
    width: 100%;
    height: auto;
  }
  .vt-grid {
    stroke: var(--border);
    stroke-width: 1;
  }
  .vt-axis {
    fill: var(--text-faint);
    font-family: var(--font-mono);
    font-size: 11px;
  }
  .vt-line {
    fill: none;
    stroke: var(--accent);
    stroke-width: 2;
    stroke-linejoin: round;
    stroke-linecap: round;
  }
  .vt-dot {
    fill: var(--accent);
    stroke: var(--surface);
    stroke-width: 2;
  }
</style>
