<script lang="ts">
  import { chartTip } from "../lib/chartTip.svelte";

  let width = $state(0);
  let height = $state(0);

  // Beside the pointer, flipped to its other side near the window's edges.
  const left = $derived(
    Math.max(8, chartTip.x + 14 + width > window.innerWidth - 8 ? chartTip.x - width - 14 : chartTip.x + 14),
  );
  const top = $derived(
    Math.max(8, chartTip.y + 14 + height > window.innerHeight - 8 ? chartTip.y - height - 14 : chartTip.y + 14),
  );
</script>

{#if chartTip.content}
  <div class="chart-tip" role="tooltip" style="left:{left}px;top:{top}px" bind:clientWidth={width} bind:clientHeight={height}>
    <div class="t-title">{chartTip.content.title}</div>
    {#if chartTip.content.subtitle}<div class="t-sub">{chartTip.content.subtitle}</div>{/if}
    {#each chartTip.content.rows as [label, value], i (i)}
      <div class="t-row"><span>{label}</span><span class="mono">{value}</span></div>
    {/each}
  </div>
{/if}

<style>
  .chart-tip {
    position: fixed;
    z-index: 50;
    pointer-events: none;
    max-width: 320px;
    padding: 9px 11px;
    border: 1px solid var(--border-strong);
    border-radius: 8px;
    background: var(--surface);
    box-shadow: var(--shadow);
    font-size: var(--fs-sm);
  }
  .t-title {
    font-weight: 600;
  }
  .t-sub {
    color: var(--text-muted);
    font-size: var(--fs-xs);
    margin-bottom: 4px;
  }
  .t-row {
    display: flex;
    justify-content: space-between;
    gap: 16px;
  }
  .t-row span:first-child {
    color: var(--text-muted);
  }
  .t-row .mono {
    font-size: var(--fs-xs);
  }
</style>
