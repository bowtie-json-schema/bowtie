<script lang="ts">
  import { chartTip } from "../lib/chartTip.svelte";
  import {
    type HeadToHead,
    type MetricKey,
    METRICS,
    betterWord,
    formatValue,
    ratioTickLabel,
    ratioTicks,
    significant,
  } from "../lib/realWorldModel";

  let {
    result,
    a,
    b,
    metric,
  }: { result: HeadToHead; a: string; b: string; metric: MetricKey } = $props();

  const kb = $derived(!!METRICS[metric].kb);

  const domain = $derived.by(() => {
    const rs = result.points.map((p) => p.ratio);
    let lo = 2 ** Math.floor(Math.log2(Math.min(1, ...rs)));
    let hi = 2 ** Math.ceil(Math.log2(Math.max(1, ...rs)));
    if (lo === hi) {
      lo /= 2;
      hi *= 2;
    }
    return { lo, hi };
  });
  const pos = (v: number) =>
    (100 * (Math.log(v) - Math.log(domain.lo))) / (Math.log(domain.hi) - Math.log(domain.lo));
  const ticks = $derived(ratioTicks(domain.lo, domain.hi));

  function onMove(event: PointerEvent) {
    const schema = (event.target as Element).closest<HTMLElement>("[data-schema]")?.dataset.schema;
    const p = schema ? result.points.find((x) => x.schema === schema) : undefined;
    if (p) tip(event, p);
    else chartTip.hide();
  }

  function tip(event: PointerEvent, p: HeadToHead["points"][number]) {
    chartTip.show(event, {
      title: p.schema,
      subtitle: METRICS[metric].long,
      rows: [
        [a, formatValue(p.a, kb)],
        [b, formatValue(p.b, kb)],
        ["", p.ratio < 1 ? `${a} ${significant(1 / p.ratio)}× ${betterWord(metric)}` : `${b} ${significant(p.ratio)}× ${betterWord(metric)}`],
      ],
    });
  }
</script>

{#if result.points.length}
  <div class="h2h" role="table" onpointermove={onMove} onpointerleave={() => chartTip.hide()} aria-label={`${a} relative to ${b} on each schema`}>
    <div class="row head" role="row">
      <span role="columnheader">Schema</span>
      <span role="columnheader" class="plot">
        {#each ticks as t (t)}<span class="tick" style="left:{pos(t)}%;transform:translateX({pos(t) > 92 ? '-100%' : pos(t) < 8 ? '0' : '-50%'})">{ratioTickLabel(t)}</span>{/each}
      </span>
    </div>
    {#each result.points as p (p.schema)}
      {@const aWins = p.ratio < 1}
      <div class="row" role="row" data-schema={p.schema}>
        <span role="cell" class="name">{p.schema}</span>
        <span role="cell" class="plot" aria-label={aWins ? `${a} ${significant(1 / p.ratio)}× ${betterWord(metric)}` : `${b} ${significant(p.ratio)}× ${betterWord(metric)}`}>
          {#each ticks as t (t)}<span class="grid" class:one={t === 1} style="left:{pos(t)}%"></span>{/each}
          <span class="stem {aWins ? 'a' : 'b'}" style="left:{Math.min(pos(1), pos(p.ratio))}%;width:{Math.abs(pos(p.ratio) - pos(1))}%"></span>
          <span class="dot {aWins ? 'a' : 'b'}" style="left:{pos(p.ratio)}%"></span>
        </span>
      </div>
    {/each}
    <div class="row foot" aria-hidden="true">
      <span></span>
      <span class="ends"><span>← {a} {betterWord(metric)}</span><span>{b} {betterWord(metric)} →</span></span>
    </div>
  </div>
{/if}

<style>
  .h2h {
    display: grid;
    grid-template-columns: minmax(110px, 190px) minmax(140px, 1fr);
    column-gap: 12px;
    font-size: var(--fs-sm);
  }
  .row {
    display: grid;
    grid-column: 1 / -1;
    grid-template-columns: subgrid;
    align-items: center;
    min-height: 22px;
    border-radius: 6px;
  }
  .row:not(.head):not(.foot):hover {
    background: var(--surface-2);
  }
  .head,
  .foot {
    color: var(--text-faint);
    font-family: var(--font-mono);
    font-size: var(--fs-2xs);
  }
  .name {
    text-align: right;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    font-size: var(--fs-xs);
  }
  .plot {
    position: relative;
    height: 100%;
    min-height: 20px;
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
  .grid.one {
    width: 2px;
    background: var(--border-strong);
  }
  .stem {
    position: absolute;
    top: 50%;
    height: 2px;
    transform: translateY(-50%);
  }
  .dot {
    position: absolute;
    top: 50%;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    transform: translate(-50%, -50%);
    box-shadow: 0 0 0 2px var(--surface);
  }
  .a {
    background: var(--bench-faster);
  }
  .b {
    background: var(--bench-slower);
  }
  .ends {
    display: flex;
    justify-content: space-between;
    padding-top: 4px;
  }
</style>
