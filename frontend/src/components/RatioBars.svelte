<script lang="ts">
  import type { Compliance } from "../data/compliance";
  import { chartTip } from "../lib/chartTip.svelte";
  import {
    type Baseline,
    type MetricKey,
    type Summary,
    METRICS,
    bestWord,
    betterWord,
    formatRatio,
    ratioTickLabel,
    ratioTicks,
    significant,
    worseWord,
  } from "../lib/realWorldModel";
  import ComplianceChip from "./ComplianceChip.svelte";

  interface Label {
    name: string;
    lang: string;
    version: string;
    /** the implementation's Bowtie page, when Bowtie tests it */
    href?: string;
  }

  let {
    summaries,
    baseline,
    metric,
    totalSchemas,
    labelFor,
    complianceFor,
    dialectName,
  }: {
    summaries: Summary[];
    baseline: Baseline;
    metric: MetricKey;
    totalSchemas: number;
    labelFor: (id: string) => Label;
    complianceFor: (id: string) => Compliance;
    dialectName: string;
  } = $props();

  const versus = $derived(baseline !== "fastest");

  // A log scale in powers of two that always includes 1×.
  const domain = $derived.by(() => {
    const finite = summaries.map((s) => s.geomean).filter(Number.isFinite);
    let lo = 2 ** Math.floor(Math.log2(Math.min(1, ...finite)));
    let hi = 2 ** Math.ceil(Math.log2(Math.max(1, ...finite)));
    if (lo === hi) hi = lo * 2;
    return { lo, hi };
  });
  const pos = (v: number) =>
    (100 * (Math.log(v) - Math.log(domain.lo))) / (Math.log(domain.hi) - Math.log(domain.lo));
  const ticks = $derived(ratioTicks(domain.lo, domain.hi));

  function bar(s: Summary) {
    const g = s.geomean;
    const from = pos(Math.min(1, g));
    const to = pos(Math.max(1, g));
    const tone = s.impl === baseline ? "base" : g < 1 ? "faster" : g > 1 ? "slower" : "level";
    return { left: from, width: Math.max(0.4, to - from), tone };
  }

  function valueText(s: Summary) {
    if (s.impl === baseline) return "baseline";
    if (versus) return formatRatio(s.geomean, metric, baseline);
    return `${significant(s.geomean)}×${s.fastestOn ? `, ${bestWord(metric)} on ${s.fastestOn}` : ""}`;
  }

  function onMove(event: PointerEvent) {
    const id = (event.target as Element).closest<HTMLElement>("[data-impl]")?.dataset.impl;
    const s = id ? summaries.find((x) => x.impl === id) : undefined;
    if (s) tip(event, s);
    else chartTip.hide();
  }

  function tip(event: PointerEvent, s: Summary) {
    const label = labelFor(s.impl);
    chartTip.show(event, {
      title: label.name,
      subtitle: [label.lang, label.version].filter(Boolean).join(" · "),
      rows: [
        ["Geometric mean", formatRatio(s.geomean, metric, baseline)],
        ["Schemas compared", `${s.compared} of ${totalSchemas}`],
        [`${bestWord(metric)[0].toUpperCase()}${bestWord(metric).slice(1)} on`, `${s.fastestOn} schema${s.fastestOn === 1 ? "" : "s"}`],
        ["Failed", String(s.failed)],
        ...(s.missing ? ([["Not run", String(s.missing)]] as [string, string][]) : []),
      ],
    });
  }
</script>

<div class="rbars" role="table" onpointermove={onMove} onpointerleave={() => chartTip.hide()} aria-label={`Geometric mean ${METRICS[metric].long}, relative to ${versus ? labelFor(baseline).name : `the ${bestWord(metric)} on each schema`}`}>
  <div class="row head" role="row">
    <span role="columnheader" class="c-name">Implementation</span>
    <span role="columnheader" class="c-chip">{dialectName}</span>
    <span role="columnheader" class="c-bar ticks">
      {#each ticks as t (t)}
        <span class="tick" style="left:{pos(t)}%;transform:translateX({pos(t) > 92 ? '-100%' : pos(t) < 8 ? '0' : '-50%'})">{ratioTickLabel(t)}</span>
      {/each}
    </span>
    <span role="columnheader" class="c-val">{versus ? `against ${labelFor(baseline).name}` : `× the ${bestWord(metric)}`}</span>
    <span role="columnheader" class="c-cov">schemas</span>
  </div>
  {#each summaries as s (s.impl)}
    {@const label = labelFor(s.impl)}
    {@const b = bar(s)}
    <div class="row" role="row" data-impl={s.impl}>
      <span role="cell" class="c-name" class:is-base={s.impl === baseline}>
        {#if label.href}<a href={label.href}>{label.name}</a>{:else}{label.name}{/if}
        <span class="lang">{label.lang}</span>
      </span>
      <span role="cell" class="c-chip"><ComplianceChip compliance={complianceFor(s.impl)} {dialectName} /></span>
      <span role="cell" class="c-bar" aria-hidden="true">
        {#each ticks as t (t)}<span class="grid" class:one={t === 1} style="left:{pos(t)}%"></span>{/each}
        {#if Number.isFinite(s.geomean)}
          <span class="bar {b.tone}" style="left:{b.left}%;width:{b.width}%"></span>
        {/if}
      </span>
      <span role="cell" class="c-val mono">{Number.isFinite(s.geomean) ? valueText(s) : "no schema completed"}</span>
      <span role="cell" class="c-cov mono" class:has-failures={s.failed > 0}>{s.compared}/{totalSchemas}</span>
    </div>
  {/each}
</div>
<p class="rbars-note">
  {#if versus}
    Bars to the left are {betterWord(metric)} than {labelFor(baseline).name}, to the right {worseWord(metric)}.
  {:else}
    1× would mean the {bestWord(metric)} of the selection on every schema.
  {/if}
  Coverage in <span class="has-failures">this colour</span> means some schemas failed to validate, and they are left out of the mean.
</p>

<style>
  .rbars {
    display: grid;
    grid-template-columns: minmax(130px, 220px) auto minmax(120px, 1fr) minmax(90px, 160px) 60px;
    column-gap: 12px;
    font-size: var(--fs-sm);
  }
  .row {
    display: grid;
    grid-column: 1 / -1;
    grid-template-columns: subgrid;
    align-items: center;
    min-height: 28px;
    border-radius: 6px;
  }
  .row:not(.head):hover {
    background: var(--surface-2);
  }
  .head {
    color: var(--text-faint);
    font-size: var(--fs-2xs);
    font-family: var(--font-mono);
    min-height: 22px;
  }
  .c-name {
    display: flex;
    align-items: baseline;
    gap: 8px;
    min-width: 0;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    padding-left: 4px;
  }
  .c-name.is-base,
  .c-name.is-base a {
    color: var(--accent);
    font-weight: 600;
  }
  .c-name a {
    color: var(--text);
  }
  .c-name a:hover {
    color: var(--accent);
  }
  .lang {
    margin-left: auto;
    font-family: var(--font-mono);
    font-size: var(--fs-2xs);
    color: var(--text-faint);
  }
  .c-bar {
    position: relative;
    height: 100%;
    min-height: 22px;
  }
  .ticks .tick {
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
  .grid.one {
    background: var(--border-strong);
    width: 2px;
  }
  .bar {
    position: absolute;
    top: 50%;
    height: 14px;
    transform: translateY(-50%);
    border-radius: 3px;
  }
  .bar.faster {
    background: var(--bench-faster);
  }
  .bar.slower {
    background: var(--bench-slower);
  }
  .bar.base {
    background: var(--accent);
  }
  .bar.level {
    background: var(--text-faint);
  }
  .c-val,
  .c-cov {
    font-size: var(--fs-xs);
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .c-cov {
    text-align: right;
    padding-right: 4px;
  }
  .has-failures {
    color: var(--fail);
  }
  .rbars-note {
    margin: 10px 0 0;
    font-size: var(--fs-xs);
    color: var(--text-muted);
  }
  @media (max-width: 640px) {
    .rbars {
      grid-template-columns: minmax(100px, 1fr) auto minmax(90px, 1.4fr) 64px;
    }
    .c-cov,
    .lang {
      display: none;
    }
  }
</style>
