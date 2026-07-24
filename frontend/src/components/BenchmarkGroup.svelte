<script lang="ts">
  import type Implementation from "../data/Implementation";
  import type { BenchmarkGroupResult } from "../data/parseBenchmarkData";
  import { benchmarkTable, formatDuration } from "../lib/benchmarkModel";

  let {
    group,
    scopedIds,
    implementations,
  }: {
    group: BenchmarkGroupResult;
    scopedIds: string[];
    implementations: Map<string, Implementation>;
  } = $props();

  let open = $state(false);
  const nameOf = (id: string) => implementations.get(id)?.name ?? id;
</script>

<details class="bench-group" bind:open>
  <summary>
    <div class="bg-title">
      <span class="bg-name">{group.name}</span>
      {#if group.varyingParameter}
        <span class="bg-vary">varying {group.varyingParameter}</span>
      {/if}
    </div>
    {#if group.description}<div class="bg-desc">{group.description}</div>{/if}
  </summary>

  {#if open}
    <div class="bg-body">
      {#each group.benchmarkResults as bench, bi (bi)}
        {@const table = benchmarkTable(bench, scopedIds)}
        <div class="bench-item">
          <div class="bi-head">{bench.name}</div>
          {#if bench.description && bench.description !== bench.name}
            <div class="bi-desc">{bench.description}</div>
          {/if}
          {#if table.rows.length === 0}
            <div class="empty-note">No results for the selected implementations.</div>
          {:else}
            <div class="table-scroll">
              <table class="bench-table">
                <thead>
                  <tr>
                    <th scope="col" class="impl">Implementation</th>
                    {#each table.tests as t, ti (ti)}<th scope="col">{t}</th>{/each}
                    <th scope="col">Geo. mean</th>
                  </tr>
                </thead>
                <tbody>
                  {#each table.rows as row, i (row.id)}
                    <tr class:best={i === 0}>
                      <th scope="row" class="impl">
                        {nameOf(row.id)}
                        {#if i === 0}<span class="fastest">fastest</span>{/if}
                      </th>
                      {#each row.cells as c, ci (ci)}
                        <td class:err={c.errored}>
                          {#if c.errored}errored{:else}{formatDuration(c.mean)} <span class="pm">± {formatDuration(c.std)}</span>{/if}
                        </td>
                      {/each}
                      <td class="gm">{formatDuration(row.geoMean)}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</details>

<style>
  .bench-group {
    border: 1px solid var(--border);
    border-radius: 11px;
    background: var(--surface);
    margin-bottom: 10px;
    overflow: hidden;
  }
  summary {
    list-style: none;
    cursor: pointer;
    padding: 12px 15px;
  }
  summary::-webkit-details-marker {
    display: none;
  }
  .bg-title {
    display: flex;
    align-items: baseline;
    gap: 10px;
  }
  .bg-name {
    font-weight: 560;
    font-size: 13.5px;
  }
  .bg-vary {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--accent);
  }
  .bg-desc {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 3px;
  }
  .bg-body {
    padding: 4px 15px 14px;
    border-top: 1px solid var(--border);
  }
  .bench-item {
    margin-top: 14px;
  }
  .bi-head {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text);
    margin-bottom: 2px;
  }
  .bi-desc {
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 8px;
  }
  .table-scroll {
    overflow-x: auto;
  }
  .bench-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }
  .bench-table th,
  .bench-table td {
    padding: 7px 10px;
    border-bottom: 1px solid var(--border);
    text-align: right;
    white-space: nowrap;
  }
  .bench-table thead th {
    color: var(--text-muted);
    font-weight: 560;
    font-size: 11px;
  }
  .bench-table th.impl {
    text-align: left;
  }
  .bench-table td,
  .bench-table tbody th {
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
  }
  .bench-table tbody th.impl {
    font-family: var(--font-sans);
    font-weight: 500;
  }
  .bench-table tr.best th,
  .bench-table tr.best td {
    background: color-mix(in srgb, var(--pass) 12%, transparent);
  }
  .fastest {
    font-family: var(--font-mono);
    font-size: 9.5px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--pass);
    margin-left: 8px;
  }
  .pm {
    color: var(--text-faint);
  }
  .gm {
    color: var(--text);
    font-weight: 600;
  }
  td.err {
    color: var(--error);
  }
</style>
