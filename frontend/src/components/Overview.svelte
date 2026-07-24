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

  // free-form run metadata: string values, or { href, text } link entries
  function asLink(v: unknown): { href: string; text: string } | null {
    if (
      v &&
      typeof v === "object" &&
      "href" in v &&
      "text" in v &&
      typeof (v as { href: unknown }).href === "string" &&
      typeof (v as { text: unknown }).text === "string"
    ) {
      return v as { href: string; text: string };
    }
    return null;
  }
  const metaEntries = $derived(
    Object.entries(data.runMetadata.metadata ?? {}).filter(
      ([, v]) => typeof v === "string" || asLink(v),
    ),
  );

  const latestDialect = (impl: (typeof report.otherImpls)[number]) =>
    impl.dialects.reduce((a, c) =>
      c.firstPublicationDate > a.firstPublicationDate ? c : a,
    );
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

{#if metaEntries.length}
  <table class="kv runmeta">
    <tbody>
      {#each metaEntries as [label, value] (label)}
        {@const link = asLink(value)}
        <tr>
          <th>{label}</th>
          <td>{#if link}<a href={link.href}>{link.text}</a>{:else}{String(value)}{/if}</td>
        </tr>
      {/each}
    </tbody>
  </table>
{/if}

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

{#if report.otherImpls.length}
  <details class="other-impls">
    <summary>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg>
      {report.otherImpls.length}
      {report.otherImpls.length === 1 ? "implementation doesn't" : "more implementations don't"}
      support {data.runMetadata.dialect.prettyName} under the current language filter
    </summary>
    <ul>
      {#each report.otherImpls as impl (impl.id)}
        <li>
          <a href="#{impl.routePath}">{impl.name}</a>
          <span class="oi-lang">{mapLanguage(impl.language)}</span>
          {#if impl.dialects.length}
            <span class="oi-latest">latest: <a href="#{latestDialect(impl).routePath}">{latestDialect(impl).prettyName}</a></span>
          {/if}
        </li>
      {/each}
    </ul>
  </details>
{/if}

<div class="hint-card">
  Select a case from the list on the right &nbsp;·&nbsp; or press
  <span class="kbd">↓</span> to start browsing
</div>

<style>
  .runmeta {
    margin: -14px 0 26px;
  }
  .other-impls {
    margin-top: 22px;
    border: 1px solid var(--border);
    border-radius: 11px;
    background: var(--surface);
    padding: 0 15px;
  }
  .other-impls summary {
    list-style: none;
    cursor: pointer;
    padding: 12px 0;
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 12.5px;
    color: var(--text-muted);
  }
  .other-impls summary::-webkit-details-marker {
    display: none;
  }
  .other-impls summary svg {
    color: var(--text-faint);
    flex: none;
  }
  .other-impls ul {
    margin: 0;
    padding: 4px 0 14px;
    list-style: none;
    display: grid;
    gap: 8px;
    border-top: 1px solid var(--border);
  }
  .other-impls li {
    font-size: 12.5px;
    display: flex;
    align-items: baseline;
    gap: 8px;
    flex-wrap: wrap;
    padding-top: 8px;
  }
  .oi-lang {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--text-faint);
  }
  .oi-latest {
    color: var(--text-muted);
    margin-left: auto;
    font-size: 11.5px;
  }
</style>
