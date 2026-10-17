<script lang="ts">
  import { chartTip } from "../lib/chartTip.svelte";
  import {
    type Baseline,
    type Cell,
    type MetricKey,
    type MetricTable,
    METRICS,
    formatRatio,
    formatValue,
    ratio,
    significant,
    valueTicksLinear,
    valueTicksLog,
  } from "../lib/realWorldModel";

  let {
    table,
    schema,
    selected,
    baseline,
    metric,
    log,
    nameOf,
    hrefOf,
  }: {
    table: MetricTable;
    schema: string;
    selected: string[];
    baseline: Baseline;
    metric: MetricKey;
    log: boolean;
    nameOf: (id: string) => string;
    hrefOf: (id: string) => string | undefined;
  } = $props();

  const kb = $derived(!!METRICS[metric].kb);

  const rows = $derived.by(() => {
    const all = selected.map((id) => ({ id, cell: table.get(id, schema) }));
    const ok = all.filter((r) => r.cell.state === "ok") as { id: string; cell: Extract<Cell, { state: "ok" }> }[];
    ok.sort((a, b) => a.cell.median - b.cell.median);
    const rest = all.filter((r) => r.cell.state !== "ok").sort((a, b) => nameOf(a.id).localeCompare(nameOf(b.id)));
    return { ok, rest };
  });

  /** The highlighted bar: the baseline, or the fastest when comparing with the fastest. */
  const reference = $derived(baseline === "fastest" ? rows.ok[0]?.id : baseline);

  const scale = $derived.by(() => {
    if (!rows.ok.length) return null;
    const min = Math.min(...rows.ok.map((r) => r.cell.min));
    const max = Math.max(...rows.ok.map((r) => r.cell.max));
    if (log) {
      const lo = 10 ** Math.floor(Math.log10(min));
      let hi = 10 ** Math.ceil(Math.log10(max));
      if (hi === lo) hi = lo * 10;
      const at = (v: number) => (100 * (Math.log(v) - Math.log(lo))) / (Math.log(hi) - Math.log(lo));
      return { at, origin: lo, ticks: valueTicksLog(lo, hi) };
    }
    const ticks = valueTicksLinear(max);
    const hi = ticks[ticks.length - 1] || max;
    return { at: (v: number) => (100 * v) / hi, origin: 0, ticks };
  });

  // Fewer labels on a short axis, so that they never run into each other.
  const labelled = $derived(scale ? scale.ticks.filter((_, i, all) => all.length <= 6 || i % 2 === 0) : []);

  function onMove(event: PointerEvent) {
    const id = (event.target as Element).closest<HTMLElement>("[data-impl]")?.dataset.impl;
    if (id) tip(event, id);
    else chartTip.hide();
  }

  function tip(event: PointerEvent, id: string) {
    const cell = table.get(id, schema);
    chartTip.show(event, {
      title: nameOf(id),
      subtitle: `${schema} · ${METRICS[metric].long}`,
      rows:
        cell.state === "ok"
          ? [
              ["Median", formatValue(cell.median, kb)],
              ["Runs", cell.runs.map((v) => formatValue(v, kb)).join(", ")],
              [
                baseline === "fastest" ? "Against the fastest" : `Against ${nameOf(baseline)}`,
                formatRatio(ratio(table, id, schema, baseline, selected), metric, baseline),
              ],
            ]
          : [["Result", cell.state === "failed" ? "failed to validate" : "not run"]],
    });
  }
</script>

{#if !scale}
  <div class="empty-note">No selected implementation completes this schema.</div>
{:else}
  <div class="sbars" role="table" onpointermove={onMove} onpointerleave={() => chartTip.hide()} aria-label={`${METRICS[metric].long} on ${schema}`}>
    <div class="row head" role="row">
      <span role="columnheader">Implementation</span>
      <span role="columnheader" class="c-bar">
        {#each labelled as t (t)}<span class="tick" style="left:{scale.at(t)}%;transform:translateX({scale.at(t) > 92 ? '-100%' : scale.at(t) < 8 ? '0' : '-50%'})">{formatValue(t, kb).replace(/\.00? /, " ")}</span>{/each}
      </span>
      <span role="columnheader">median</span>
    </div>
    {#each rows.ok as { id, cell } (id)}
      {@const href = hrefOf(id)}
      {@const r = ratio(table, id, schema, baseline, selected)}
      <div class="row" role="row" data-impl={id}>
        <span role="cell" class="c-name" class:is-ref={id === reference}>{#if href}<a {href}>{nameOf(id)}</a>{:else}{nameOf(id)}{/if}</span>
        <span role="cell" class="c-bar" aria-hidden="true">
          {#each scale.ticks as t (t)}<span class="grid" style="left:{scale.at(t)}%"></span>{/each}
          <span class="bar" class:ref={id === reference} style="width:{Math.max(0.4, scale.at(cell.median) - scale.at(scale.origin))}%"></span>
          {#if cell.max > cell.min}
            <span class="whisker" style="left:{scale.at(cell.min)}%;width:{scale.at(cell.max) - scale.at(cell.min)}%"></span>
          {/if}
        </span>
        <span role="cell" class="c-val mono">{formatValue(cell.median, kb)}{#if id !== reference && Number.isFinite(r)}<span class="mult">{significant(r)}×</span>{/if}</span>
      </div>
    {/each}
    {#each rows.rest as { id, cell } (id)}
      <div class="row" role="row">
        <span role="cell" class="c-name">{nameOf(id)}</span>
        <span role="cell" class="c-bar"><span class="none">{cell.state === "failed" ? "failed to validate" : "not run"}</span></span>
        <span role="cell"></span>
      </div>
    {/each}
  </div>
{/if}

<style>
  .sbars {
    display: grid;
    grid-template-columns: minmax(120px, 220px) minmax(120px, 1fr) minmax(90px, 150px);
    column-gap: 12px;
    font-size: var(--fs-sm);
  }
  .row {
    display: grid;
    grid-column: 1 / -1;
    grid-template-columns: subgrid;
    align-items: center;
    min-height: 26px;
    border-radius: 6px;
  }
  .row:not(.head):hover {
    background: var(--surface-2);
  }
  .head {
    color: var(--text-faint);
    font-family: var(--font-mono);
    font-size: var(--fs-2xs);
    min-height: 22px;
  }
  .c-name {
    padding-left: 4px;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
  .c-name a {
    color: var(--text);
  }
  .c-name a:hover {
    color: var(--accent);
  }
  .c-name.is-ref,
  .c-name.is-ref a {
    color: var(--accent);
    font-weight: 600;
  }
  .c-bar {
    position: relative;
    height: 100%;
    min-height: 22px;
  }
  .tick {
    position: absolute;
    white-space: nowrap;
  }
  .grid {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 1px;
    background: var(--border);
  }
  .bar {
    position: absolute;
    left: 0;
    top: 50%;
    height: 12px;
    transform: translateY(-50%);
    border-radius: 3px;
    background: color-mix(in srgb, var(--accent) 38%, transparent);
  }
  .bar.ref {
    background: var(--accent);
  }
  .whisker {
    position: absolute;
    top: 50%;
    height: 8px;
    transform: translateY(-50%);
    border-left: 1.5px solid var(--text);
    border-right: 1.5px solid var(--text);
    background: linear-gradient(var(--text), var(--text)) center / 100% 1.5px no-repeat;
  }
  .c-val {
    font-size: var(--fs-xs);
    color: var(--text-muted);
    white-space: nowrap;
  }
  .mult {
    margin-left: 0.6em;
    color: var(--text-faint);
  }
  .none {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    font-size: var(--fs-xs);
    color: var(--text-muted);
  }
</style>
