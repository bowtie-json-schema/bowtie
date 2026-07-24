<script lang="ts">
  import type Dialect from "../data/Dialect";
  import type { ReportData } from "../data/parseReportData";
  import { failuresFor } from "../lib/reportModel";
  import FailureItem from "./FailureItem.svelte";

  let {
    reports,
    implId,
    implName,
  }: {
    reports: Map<Dialect, ReportData>;
    implId: string;
    implName: string;
  } = $props();

  // dialects (newest first) whose report includes this implementation
  const dialects = $derived(
    [...reports.entries()]
      .filter(([, rd]) => rd.implementationsResults.has(implId))
      .map(([d]) => d)
      .sort((a, b) => a.compare(b)),
  );

  // default to the supported dialect with the most failures (where the action is)
  const defaultDialect = $derived.by<Dialect | undefined>(() => {
    let best: Dialect | undefined;
    let bestN = -1;
    for (const d of dialects) {
      const n = failuresFor(reports.get(d)!, implId).length;
      if (n > bestN) {
        bestN = n;
        best = d;
      }
    }
    return best;
  });

  let chosen = $state<string | null>(null);
  const active = $derived(
    dialects.find((d) => d.shortName === chosen) ?? defaultDialect,
  );
  const failures = $derived(active ? failuresFor(reports.get(active)!, implId) : []);
</script>

<div class="card">
  <header class="ff-head">
    <span>Failures</span>
    {#if dialects.length > 1 && active}
      <select
        class="ff-select mono"
        value={active.shortName}
        onchange={(e) => (chosen = (e.target as HTMLSelectElement).value)}
        aria-label="Dialect for failures"
      >
        {#each dialects as d (d.shortName)}
          <option value={d.shortName}>{d.prettyName}</option>
        {/each}
      </select>
    {/if}
  </header>
  <div class="body">
    {#if !active}
      <div class="empty-note">{implName} isn't included in any dialect report.</div>
    {:else if failures.length === 0}
      <div class="empty-note">{implName} passes every test on {active.prettyName}.</div>
    {:else}
      <p class="ff-count">
        <b>{failures.length}</b> unsuccessful {failures.length === 1 ? "test" : "tests"} on {active.prettyName}
      </p>
      {#each failures as f, i (i)}
        <FailureItem failure={f} />
      {/each}
    {/if}
  </div>
</div>

<style>
  .ff-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .ff-select {
    border: 1px solid var(--border-strong);
    border-radius: 7px;
    background: var(--surface);
    color: var(--text);
    font-size: 12px;
    padding: 4px 8px;
    cursor: pointer;
  }
  .ff-count {
    font-size: 12.5px;
    color: var(--text-muted);
    margin: 0 0 14px;
  }
  .ff-count b {
    color: var(--text);
    font-variant-numeric: tabular-nums;
  }
</style>
