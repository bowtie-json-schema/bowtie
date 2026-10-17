<script lang="ts">
  import type { RealWorldSchema } from "../data/realWorldBenchmarks";
  import { chartTip } from "../lib/chartTip.svelte";
  import {
    type Baseline,
    type MetricKey,
    type MetricTable,
    METRICS,
    bestWord,
    formatRatio,
    formatValue,
    ratio,
    ratioIntensity,
    significant,
  } from "../lib/realWorldModel";

  let {
    table,
    schemas,
    columns,
    baseline,
    selected,
    metric,
    showMedian,
    nameOf,
    current,
    onSchema,
  }: {
    table: MetricTable;
    schemas: RealWorldSchema[];
    /** implementation IDs, in the order to show them */
    columns: string[];
    baseline: Baseline;
    selected: string[];
    metric: MetricKey;
    /** show each median instead of its ratio */
    showMedian: boolean;
    nameOf: (id: string) => string;
    current: string;
    onSchema: (name: string) => void;
  } = $props();

  const kb = $derived(!!METRICS[metric].kb);

  function fill(r: number) {
    const t = ratioIntensity(r, baseline);
    const pole = t < 0 ? "var(--bench-faster-fill)" : "var(--bench-slower-fill)";
    return `color-mix(in oklab, ${pole} ${Math.round(Math.abs(t) * 100)}%, var(--surface-2))`;
  }

  function onMove(event: PointerEvent) {
    const key = (event.target as Element).closest<HTMLElement>("[data-cell]")?.dataset.cell;
    if (!key) return chartTip.hide();
    const at = key.indexOf("\u0000");
    tip(event, key.slice(0, at), key.slice(at + 1));
  }

  function tip(event: PointerEvent, impl: string, schema: string) {
    const cell = table.get(impl, schema);
    chartTip.show(event, {
      title: nameOf(impl),
      subtitle: `${schema} · ${METRICS[metric].long}`,
      rows:
        cell.state === "ok"
          ? [
              ["Median", formatValue(cell.median, kb)],
              ["Range", `${formatValue(cell.min, kb)} – ${formatValue(cell.max, kb)}`],
              [
                baseline === "fastest" ? `Against the ${bestWord(metric)}` : `Against ${nameOf(baseline)}`,
                formatRatio(ratio(table, impl, schema, baseline, selected), metric, baseline),
              ],
            ]
          : [["Result", cell.state === "failed" ? "failed to validate" : "not run"]],
    });
  }
</script>

<div class="matrix-scroll">
  <table class="rmatrix" onpointermove={onMove} onpointerleave={() => chartTip.hide()}>
    <caption class="sr-only">
      {METRICS[metric].long} on each schema, {showMedian ? "as the median" : "as a multiple"}{baseline === "fastest"
        ? ` of the ${bestWord(metric)} of the selection`
        : ` of ${nameOf(baseline)}`}
    </caption>
    <thead>
      <tr>
        <th scope="col" class="corner">Schema</th>
        {#each columns as id (id)}
          <th scope="col" class:base={id === baseline}><span>{nameOf(id)}</span></th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each schemas as s (s.name)}
        <tr class:current={s.name === current}>
          <th scope="row">
            <button type="button" onclick={() => onSchema(s.name)}>{s.name}</button>
          </th>
          {#each columns as id (id)}
            {@const cell = table.get(id, s.name)}
            {#if cell.state === "ok"}
              {@const r = ratio(table, id, s.name, baseline, selected)}
              <td data-cell={`${id}\u0000${s.name}`} style={Number.isFinite(r) ? `background:${fill(r)}` : ""}>{showMedian ? formatValue(cell.median, kb) : Number.isFinite(r) ? significant(r) : "–"}</td>
            {:else}
              <td data-cell={`${id}\u0000${s.name}`} class={cell.state}>{cell.state === "failed" ? "✕" : "·"}<span class="sr-only">{cell.state === "failed" ? "failed" : "not run"}</span></td>
            {/if}
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .matrix-scroll {
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  .rmatrix {
    border-collapse: separate;
    border-spacing: 2px;
    font-family: var(--font-mono);
    font-size: var(--fs-2xs);
    font-variant-numeric: tabular-nums;
  }
  thead th {
    vertical-align: bottom;
    height: 140px;
    padding: 4px 0;
    font-weight: 500;
    color: var(--text-muted);
  }
  thead th span {
    display: block;
    margin: 0 auto;
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    white-space: nowrap;
    font-family: var(--font-sans);
    font-size: var(--fs-xs);
  }
  thead th.base span {
    color: var(--accent);
    font-weight: 600;
  }
  th.corner,
  tbody th {
    position: sticky;
    left: 0;
    z-index: 1;
    background: var(--surface);
    text-align: left;
  }
  th.corner {
    padding-left: 8px;
    font-family: var(--font-sans);
    font-size: var(--fs-xs);
    color: var(--text-faint);
  }
  tbody th button {
    all: unset;
    cursor: pointer;
    padding: 0 10px 0 8px;
    font-family: var(--font-sans);
    font-size: var(--fs-sm);
    white-space: nowrap;
    color: var(--text);
  }
  tbody th button:hover,
  tr.current th button {
    color: var(--accent);
  }
  tbody th button:focus-visible {
    outline: 2px solid var(--accent);
  }
  td {
    min-width: 40px;
    height: 24px;
    padding: 0 3px;
    text-align: center;
    border-radius: 3px;
    color: var(--text);
  }
  td.failed {
    color: var(--text-muted);
    background: repeating-linear-gradient(45deg, var(--surface-2) 0 3px, var(--surface) 3px 6px);
  }
  td.missing {
    color: var(--text-faint);
  }
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
  }
</style>
