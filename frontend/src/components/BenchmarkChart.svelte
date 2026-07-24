<script lang="ts">
  interface Item {
    label: string;
    value: number;
  }

  let {
    items,
    format,
  }: { items: Item[]; format: (n: number) => string } = $props();

  const max = $derived(Math.max(1e-9, ...items.map((i) => i.value)));
</script>

<div class="bchart">
  {#each items as it, i (i)}
    <div class="brow">
      <div class="blabel" title={it.label}>{it.label}</div>
      <div class="btrack">
        <div
          class="bfill {i === 0 ? 'best' : ''}"
          style="width:{(it.value / max) * 100}%"
        ></div>
      </div>
      <div class="bval">{format(it.value)}</div>
    </div>
  {/each}
</div>

<style>
  .bchart {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .brow {
    display: grid;
    grid-template-columns: minmax(120px, 210px) 1fr 70px;
    align-items: center;
    gap: 12px;
  }
  .blabel {
    font-size: 12.5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--text);
  }
  .btrack {
    height: 16px;
    border-radius: 5px;
    background: var(--surface-2);
    overflow: hidden;
  }
  .bfill {
    height: 100%;
    border-radius: 5px;
    background: color-mix(in srgb, var(--accent) 42%, transparent);
    min-width: 2px;
    transition: width 0.2s;
  }
  .bfill.best {
    background: var(--accent);
  }
  .bval {
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    font-size: 11.5px;
    color: var(--text-muted);
    text-align: right;
  }
</style>
