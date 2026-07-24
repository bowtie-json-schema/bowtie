<script lang="ts">
  import Dialect from "../data/Dialect";
  import { router } from "../stores/router.svelte";

  let { current, base }: { current: string; base: string } = $props();

  const dialects = Dialect.newestToOldest();

  function onChange(e: Event) {
    router.navigate(`${base}/${(e.target as HTMLSelectElement).value}`);
  }
</script>

<label class="dialect-picker">
  <span class="label">Dialect</span>
  <div class="dp-select">
    <select value={current} onchange={onChange} aria-label="Choose dialect">
      {#each dialects as d (d.shortName)}
        <option value={d.shortName}>{d.prettyName}</option>
      {/each}
    </select>
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
  </div>
</label>

<style>
  .dialect-picker {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .dp-select {
    position: relative;
    display: flex;
    align-items: center;
  }
  .dp-select select {
    appearance: none;
    width: 100%;
    font-family: var(--font-mono);
    font-size: 12.5px;
    color: var(--text);
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: 8px;
    padding: 7px 30px 7px 11px;
    cursor: pointer;
  }
  .dp-select select:focus-visible {
    border-color: var(--accent);
  }
  .dp-select svg {
    position: absolute;
    right: 10px;
    color: var(--text-faint);
    pointer-events: none;
  }
</style>
