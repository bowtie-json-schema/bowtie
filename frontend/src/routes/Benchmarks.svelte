<script lang="ts">
  import { titleCase } from "title-case";

  import Dialect from "../data/Dialect";
  import { mapLanguage } from "../data/mapLanguage";
  import type { BenchmarkReportData } from "../data/parseBenchmarkData";
  import {
    benchmarkLanguages,
    benchmarkTypes,
    formatDuration,
    overallRanking,
  } from "../lib/benchmarkModel";
  import BenchmarkChart from "../components/BenchmarkChart.svelte";
  import BenchmarkGroup from "../components/BenchmarkGroup.svelte";
  import Spinner from "../components/Spinner.svelte";

  let { draftName }: { draftName?: string } = $props();

  let data = $state<BenchmarkReportData | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let loadToken = 0;

  // filters (arrays; reassigned on toggle)
  let langs = $state<string[]>([]);
  let types = $state<string[]>([]);

  async function load(name?: string) {
    const token = ++loadToken;
    loading = true;
    error = null;
    try {
      const dialect = name ? Dialect.withName(name) : Dialect.latest();
      document.title = `Bowtie – ${dialect.prettyName} benchmarks`;
      const report = await dialect.fetchBenchmarkReport();
      if (token !== loadToken) return;
      data = report;
      langs = benchmarkLanguages(report.metadata.implementations);
      types = benchmarkTypes(report.results);
    } catch (e) {
      if (token === loadToken)
        error = e instanceof Error ? e.message : String(e);
    } finally {
      if (token === loadToken) loading = false;
    }
  }

  $effect(() => {
    void load(draftName);
  });

  const allLanguages = $derived(
    data ? benchmarkLanguages(data.metadata.implementations) : [],
  );
  const allTypes = $derived(data ? benchmarkTypes(data.results) : []);

  const scopedIds = $derived(
    data
      ? [...data.metadata.implementations]
          .filter(([, i]) => langs.includes(i.language))
          .map(([id]) => id)
      : [],
  );

  const filteredGroups = $derived(
    data ? data.results.filter((g) => types.includes(g.benchmarkType)) : [],
  );

  const ranking = $derived(
    data
      ? overallRanking(filteredGroups, scopedIds).map((r) => ({
          label: data!.metadata.implementations.get(r.id)?.name ?? r.id,
          value: r.geoMean,
        }))
      : [],
  );

  const groupsByType = $derived.by(() => {
    const out: Record<string, typeof filteredGroups> = {};
    for (const g of filteredGroups) (out[g.benchmarkType] ??= []).push(g);
    return out;
  });

  const toggle = (arr: string[], v: string) =>
    arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];
</script>

{#if loading}
  <Spinner />
{:else if error}
  <div class="doc"><div class="doc-inner">
    <h1 class="page">Benchmarks</h1>
    <div class="empty-note">Couldn't load benchmarks.<br />{error}</div>
  </div></div>
{:else if data}
  <div class="doc">
    <div class="doc-inner">
      <div class="crumbs"><a href="#/">Report</a><span class="sep">/</span><span>Benchmarks</span></div>
      <h1 class="page">{data.metadata.dialect.prettyName} benchmarks</h1>

      <div class="card">
        <header>Run info</header>
        <div class="body">
          <table class="kv">
            <tbody>
              <tr><th>Dialect</th><td class="mono">{data.metadata.dialect.uri}</td></tr>
              <tr><th>Ran</th><td>{data.metadata.ago()}</td></tr>
              {#if data.metadata.systemMetadata.cpuModel}
                <tr><th>CPU</th><td>{data.metadata.systemMetadata.cpuModel}{#if data.metadata.systemMetadata.cpuFreq} <span class="muted">({data.metadata.systemMetadata.cpuFreq})</span>{/if}</td></tr>
              {/if}
              {#if data.metadata.systemMetadata.cpuCount}
                <tr><th>CPU count</th><td class="mono">{data.metadata.systemMetadata.cpuCount}</td></tr>
              {/if}
              {#if data.metadata.systemMetadata.hostname}
                <tr><th>Hostname</th><td class="mono">{data.metadata.systemMetadata.hostname}</td></tr>
              {/if}
              <tr><th>Platform</th><td class="mono">{data.metadata.systemMetadata.platform}</td></tr>
              <tr><th>pyperf</th><td class="mono">{data.metadata.systemMetadata.perfVersion}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <header>Filtering</header>
        <div class="body">
          <span class="label" style="display:block;margin-bottom:8px">Language</span>
          <div class="chips">
            {#each allLanguages as lang (lang)}
              <button class="chip" aria-pressed={langs.includes(lang)} onclick={() => (langs = toggle(langs, lang))}>{mapLanguage(lang)}</button>
            {/each}
          </div>
          <span class="label" style="display:block;margin:14px 0 8px">Benchmark type</span>
          <div class="chips">
            {#each allTypes as type (type)}
              <button class="chip" aria-pressed={types.includes(type)} onclick={() => (types = toggle(types, type))}>{titleCase(type)}</button>
            {/each}
          </div>
        </div>
      </div>

      <div class="card">
        <header>Overall speed · geometric mean, shorter is better</header>
        <div class="body">
          {#if ranking.length === 0}
            <div class="empty-note">No benchmark results for the selected filters.</div>
          {:else}
            <BenchmarkChart items={ranking} format={formatDuration} />
          {/if}
        </div>
      </div>

      {#each allTypes.filter((t) => types.includes(t) && groupsByType[t]) as type (type)}
        <h2 class="bench-type-head">{titleCase(type)}</h2>
        {#each groupsByType[type] as group, gi (gi)}
          <BenchmarkGroup {group} {scopedIds} implementations={data.metadata.implementations} />
        {/each}
      {/each}
    </div>
  </div>
{/if}

<style>
  .muted {
    color: var(--text-muted);
  }
  .bench-type-head {
    font-size: 15px;
    font-weight: 620;
    letter-spacing: -0.01em;
    margin: 26px 0 12px;
  }
</style>
