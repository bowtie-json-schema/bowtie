<script lang="ts">
  import { report } from "../stores/report.svelte";
  import { router } from "../stores/router.svelte";
  import { mapLanguage } from "../data/mapLanguage";

  const data = $derived(report.data!);

  const totalTests = $derived(
    [...data.cases.values()].reduce((n, c) => n + c.tests.length, 0),
  );

  interface Row {
    id: string;
    name: string;
    language: string;
    version?: string;
    ok: number;
    fail: number;
    err: number;
    skip: number;
    bad: number;
  }

  const rows = $derived.by<Row[]>(() => {
    const out: Row[] = [];
    for (const id of report.scopedImplIds) {
      const impl = data.runMetadata.implementations.get(id)!;
      const t = data.implementationsResults.get(id)!.totals;
      const fail = t.failedTests ?? 0;
      const err = t.erroredTests ?? 0;
      const skip = t.skippedTests ?? 0;
      const bad = fail + err + skip;
      out.push({
        id,
        name: impl.name,
        language: impl.language,
        version: impl.version,
        ok: totalTests - bad,
        fail,
        err,
        skip,
        bad,
      });
    }
    return out.sort((a, b) => a.bad - b.bad);
  });

  const pct = (n: number) => (totalTests ? (n / totalTests) * 100 : 0);
</script>

<div class="crumbs"><span>Report</span></div>
<h1 class="page">{data.runMetadata.dialect.prettyName} compliance</h1>
<p class="h-lead">
  How each implementation does against the official JSON Schema Test Suite. Pick
  a case on the right to inspect who disagrees, and why.
</p>

<div class="runstrip">
  <div class="cell">
    <span class="label">Dialect</span>
    <div class="v small">{data.runMetadata.dialect.uri.replace(/^https?:\/\//, "")}</div>
  </div>
  <div class="cell">
    <span class="label">Implementations</span>
    <div class="v">{report.scopedImplIds.length}</div>
  </div>
  <div class="cell"><span class="label">Cases</span><div class="v">{data.cases.size}</div></div>
  <div class="cell"><span class="label">Tests</span><div class="v">{totalTests}</div></div>
  <div class="cell"><span class="label">Ran</span><div class="v small">{data.runMetadata.ago()}</div></div>
</div>

{#if data.didFailFast}
  <div class="alert-failfast">
    <svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
    </svg>
    <span>This run failed fast, so some input cases may not have been executed — implementations with missing results are shown as errored.</span>
  </div>
{/if}

<span class="label sec-label">Implementations · fewest issues first</span>
<div class="matrix">
  {#each rows as r (r.id)}
    <button class="row" onclick={() => router.navigate(`/implementations/${r.id}`)}>
      <div class="who">
        <span class="nm">{r.name}</span>
        <span class="lg">{mapLanguage(r.language)}</span>
        {#if r.version}<span class="vv">{r.version}</span>{/if}
      </div>
      <div class="bar">
        {#if r.ok}<i style="width:{pct(r.ok)}%;background:var(--pass)"></i>{/if}
        {#if r.fail}<i style="width:{pct(r.fail)}%;background:var(--fail)"></i>{/if}
        {#if r.err}<i style="width:{pct(r.err)}%;background:var(--error)"></i>{/if}
        {#if r.skip}<i style="width:{pct(r.skip)}%;background:var(--skip)"></i>{/if}
      </div>
      <div class="count {r.bad ? 'some' : 'zero'}">{r.bad}</div>
    </button>
  {/each}
</div>

<div class="hint-card">
  Select a case from the list on the right &nbsp;·&nbsp; or press
  <span class="kbd">↓</span> to start browsing
</div>
