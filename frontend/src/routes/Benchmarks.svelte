<script lang="ts">
  import dayjs from "dayjs";
  import relativeTime from "dayjs/plugin/relativeTime";

  import Dialect from "../data/Dialect";
  import { type Compliance, fetchCompliance, isFullyCompliant } from "../data/compliance";
  import {
    BENCHMARK_REPOSITORY,
    type RealWorldData,
    fetchRealWorldData,
  } from "../data/realWorldBenchmarks";
  import { chartTip } from "../lib/chartTip.svelte";
  import {
    type Baseline,
    type MetricKey,
    METRICS,
    MetricTable,
    betterWord,
    headToHead,
    rank,
    significant,
    spread,
    worseWord,
  } from "../lib/realWorldModel";
  import ChartTip from "../components/ChartTip.svelte";
  import ComplianceChip from "../components/ComplianceChip.svelte";
  import DialectPicker from "../components/DialectPicker.svelte";
  import HeadToHeadChart from "../components/HeadToHeadChart.svelte";
  import RatioBars from "../components/RatioBars.svelte";
  import RatioMatrix from "../components/RatioMatrix.svelte";
  import SchemaBars from "../components/SchemaBars.svelte";
  import Spinner from "../components/Spinner.svelte";

  dayjs.extend(relativeTime);

  let { draftName }: { draftName?: string } = $props();

  let data = $state<RealWorldData | null>(null);
  let error = $state<string | null>(null);

  $effect(() => {
    document.title = "Bowtie – Real-world benchmarks";
    fetchRealWorldData()
      .then((loaded) => (data = loaded))
      .catch((e: unknown) => (error = e instanceof Error ? e.message : String(e)));
  });

  // Without a dialect in the address, the one most of the benchmark's schemas declare.
  const dialect = $derived.by(() => {
    if (draftName) return Dialect.withName(draftName);
    const counts: Record<string, number> = {};
    for (const s of data?.schemas ?? []) if (s.dialect) counts[s.dialect] = (counts[s.dialect] ?? 0) + 1;
    const common = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0];
    try {
      return common ? Dialect.forURI(common) : Dialect.latest();
    } catch {
      return Dialect.latest();
    }
  });

  // Each implementation's compliance on the dialect, from its Bowtie badge; reloaded when the dialect changes.
  let compliance = $state(new Map<string, Compliance>());
  let complianceLoaded = $state(false);
  let complianceToken = 0;
  $effect(() => {
    if (!data) return;
    const token = ++complianceToken;
    const current = dialect;
    complianceLoaded = false;
    const ids = data.impls.flatMap((i) => (i.bowtie ? [i.bowtie] : []));
    void fetchCompliance(ids, current).then((loaded) => {
      if (token !== complianceToken) return;
      compliance = loaded;
      complianceLoaded = true;
    });
  });

  const implById = $derived(new Map((data?.impls ?? []).map((i) => [i.id, i])));
  const nameOf = (id: string) => implById.get(id)?.name ?? id;
  const hrefOf = (id: string) => {
    const bowtie = implById.get(id)?.bowtie;
    return bowtie ? `#/implementations/${bowtie}` : undefined;
  };
  const complianceFor = (id: string): Compliance => {
    const bowtie = implById.get(id)?.bowtie;
    if (!bowtie) return { state: "untested" };
    return compliance.get(bowtie) ?? { state: "unknown" };
  };

  /* ---------- filters ---------- */

  let metric = $state<MetricKey>("warm");
  let baseline = $state<Baseline>("fastest");
  let onlyCompliant = $state(false);
  // empty = all (first click narrows, further clicks add), as on Bowtie's other pages
  let langs = $state<string[]>([]);
  let chosen = $state<string[]>([]);
  const toggle = (list: string[], v: string) => (list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);

  const allLangs = $derived([...new Set((data?.impls ?? []).map((i) => i.lang || "Other"))].sort());

  const selected = $derived(
    (data?.impls ?? [])
      .filter((i) => langs.length === 0 || langs.includes(i.lang || "Other"))
      .filter((i) => chosen.length === 0 || chosen.includes(i.id))
      .filter((i) => !onlyCompliant || isFullyCompliant(complianceFor(i.id)))
      .map((i) => i.id),
  );

  // A baseline that the filters remove falls back to the fastest on each schema.
  const effectiveBaseline = $derived<Baseline>(
    baseline !== "fastest" && !selected.includes(baseline) ? "fastest" : baseline,
  );

  const table = $derived(data ? new MetricTable(data, metric) : null);
  const ranking = $derived(table && data ? rank(table, data.schemas, effectiveBaseline, selected, nameOf) : []);

  /* ---------- by schema ---------- */

  let order = $state<"name" | "docs" | "size" | "spread">("name");
  let showMedian = $state(false);
  const orderedSchemas = $derived.by(() => {
    if (!data || !table) return [];
    const list = data.schemas.slice();
    if (order === "name") list.sort((a, b) => a.name.localeCompare(b.name));
    if (order === "docs") list.sort((a, b) => (b.docs ?? 0) - (a.docs ?? 0));
    if (order === "size") list.sort((a, b) => (b.sizeKb ?? 0) - (a.sizeKb ?? 0));
    if (order === "spread") list.sort((a, b) => spread(table, b.name, selected) - spread(table, a.name, selected));
    return list;
  });

  /* ---------- one schema ---------- */

  let schemaName = $state("");
  let logScale = $state(true);
  const currentSchema = $derived(schemaName || data?.schemas[0]?.name || "");
  const schemaInfo = $derived(data?.schemas.find((s) => s.name === currentSchema));
  function showSchema(name: string) {
    schemaName = name;
    document.getElementById("schema-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* ---------- head to head ---------- */

  let pickA = $state("");
  let pickB = $state("");
  const a = $derived(pickA || ranking[0]?.impl || "");
  const b = $derived(pickB || ranking.find((s) => s.impl !== a)?.impl || "");
  const h2h = $derived(table && data && a && b ? headToHead(table, data.schemas, a, b) : null);

  /* ---------- run info ---------- */

  const schemasByDialect = $derived.by(() => {
    const counts: Record<string, number> = {};
    for (const s of data?.schemas ?? []) {
      let name = s.dialect ?? "no $schema";
      try {
        if (s.dialect) name = Dialect.forURI(s.dialect).prettyName;
      } catch {
        // a dialect the site does not know keeps its URI
      }
      counts[name] = (counts[name] ?? 0) + 1;
    }
    return Object.entries(counts)
      .map(([name, n]) => `${n} ${name}`)
      .join(", ");
  });
  const linkedCount = $derived((data?.impls ?? []).filter((i) => i.bowtie).length);
  const ranAgo = $derived(data?.meta.date ? dayjs(data.meta.date).fromNow() : null);
</script>

{#if error}
  <div class="doc"><div class="doc-inner">
    <h1 class="page">Real-world benchmarks</h1>
    <div class="empty-note">
      Couldn’t load the benchmark results.<br />{error}<br />
      <a href={BENCHMARK_REPOSITORY}>See the benchmark on GitHub</a>
    </div>
  </div></div>
{:else if !data || !table}
  <Spinner />
{:else}
  <div class="doc">
    <div class="doc-inner">
      <div class="page-head">
        <h1 class="page">Real-world benchmarks</h1>
        <DialectPicker current={dialect.shortName} base="/benchmarks" />
      </div>
      <p class="h-lead">
        How fast JSON Schema implementations validate real-world schemas and instances, from Sourcemeta’s
        <a href={BENCHMARK_REPOSITORY}>jsonschema-benchmark</a>, alongside how each one fares in Bowtie on
        {dialect.prettyName}. Choose a measure and the implementations to compare; every chart follows.
      </p>

      <div class="card">
        <header>Run info</header>
        <div class="body">
          <table class="kv">
            <tbody>
              <tr><th>Source</th><td><a href={BENCHMARK_REPOSITORY}>sourcemeta-research/jsonschema-benchmark</a></td></tr>
              {#if data.meta.date}
                <tr><th>Ran</th><td>{ranAgo}{#if data.meta.runUrl} · <a href={data.meta.runUrl}>workflow run</a>{/if}</td></tr>
              {/if}
              {#if data.meta.commit}
                <tr><th>Commit</th><td class="mono"><a href={`https://github.com/${data.meta.repo}/commit/${data.meta.commit}`}>{data.meta.commit.slice(0, 10)}</a></td></tr>
              {/if}
              {#if data.meta.runner}<tr><th>Machines</th><td>{data.meta.runner}</td></tr>{/if}
              <tr><th>Schemas</th><td>{schemasByDialect}</td></tr>
              <tr><th>Implementations</th><td>{data.impls.length}, of which Bowtie tests {linkedCount}</td></tr>
              <tr><th>Runs</th><td>{data.meta.runs} of each, in a fresh container; the median is shown</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <header>Filtering</header>
        <div class="body filters">
          <div>
            <span class="label">Measure</span>
            <div class="chips">
              {#each Object.entries(METRICS) as [key, m] (key)}
                <button class="chip" aria-pressed={metric === key} onclick={() => (metric = key as MetricKey)}>{m.label}</button>
              {/each}
            </div>
          </div>
          <div>
            <label class="label" for="baseline">Compare with</label>
            <select id="baseline" class="select" bind:value={baseline}>
              <option value="fastest">The fastest on each schema</option>
              {#each data.impls as i (i.id)}<option value={i.id}>{i.name}</option>{/each}
            </select>
          </div>
          <div>
            <span class="label">Bowtie compliance</span>
            <div class="chips">
              <button class="chip" aria-pressed={onlyCompliant} onclick={() => (onlyCompliant = !onlyCompliant)}>
                Only 100% on {dialect.prettyName}
              </button>
            </div>
            <p class="hint">
              {#if !complianceLoaded}
                Loading Bowtie’s results for {dialect.prettyName}…
              {:else}
                {data.impls.filter((i) => isFullyCompliant(complianceFor(i.id))).length} of {data.impls.length} pass
                every Bowtie test of {dialect.prettyName}. Implementations Bowtie does not test are left out by this
                filter; change the dialect above.
              {/if}
            </p>
          </div>
          <div>
            <span class="label">Language</span>
            <div class="chips">
              {#each allLangs as lang (lang)}
                <button class="chip" aria-pressed={langs.includes(lang)} onclick={() => (langs = toggle(langs, lang))}>{lang}</button>
              {/each}
            </div>
          </div>
          <div>
            <span class="label">Implementations · {selected.length} of {data.impls.length} shown</span>
            <div class="chips">
              {#each data.impls as i (i.id)}
                <button class="chip impl-chip" aria-pressed={chosen.includes(i.id)} onclick={() => (chosen = toggle(chosen, i.id))}>
                  {i.name}
                  <ComplianceChip compliance={complianceFor(i.id)} dialectName={dialect.prettyName} />
                </button>
              {/each}
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <header>Overall · {METRICS[metric].long}, geometric mean across schemas</header>
        <div class="body">
          {#if ranking.length === 0}
            <div class="empty-note">No implementation matches the filters.</div>
          {:else}
            <RatioBars
              summaries={ranking}
              baseline={effectiveBaseline}
              {metric}
              totalSchemas={data.schemas.length}
              labelFor={(id) => ({ name: nameOf(id), lang: implById.get(id)?.lang ?? "", version: implById.get(id)?.version.split(" ")[0] ?? "", href: hrefOf(id) })}
              {complianceFor}
              dialectName={dialect.prettyName}
            />
          {/if}
        </div>
      </div>

      <div class="card">
        <header class="split">
          <span>By schema</span>
          <span class="controls">
            <label class="inline"><span class="label">Order</span>
              <select class="select" bind:value={order}>
                <option value="name">Name</option><option value="docs">Instances</option>
                <option value="size">Schema size</option><option value="spread">Spread</option>
              </select>
            </label>
            <button class="chip" aria-pressed={showMedian} onclick={() => (showMedian = !showMedian)}>Medians</button>
          </span>
        </header>
        <div class="body">
          <p class="hint">
            {showMedian ? "The median of each implementation on each schema" : effectiveBaseline === "fastest"
              ? "Each implementation as a multiple of the fastest selected implementation on each schema"
              : `Each implementation as a multiple of ${nameOf(effectiveBaseline)}: below 1 is ${betterWord(metric)}, above ${worseWord(metric)}`}.
            Darker is further from level; ✕ failed to validate, · not run. Choose a schema for its detail.
          </p>
          <RatioMatrix
            {table}
            schemas={orderedSchemas}
            columns={ranking.map((s) => s.impl)}
            baseline={effectiveBaseline}
            {selected}
            {metric}
            {showMedian}
            {nameOf}
            current={currentSchema}
            onSchema={showSchema}
          />
        </div>
      </div>

      <div class="card" id="schema-detail">
        <header class="split">
          <label class="inline"><span>Schema</span>
            <select class="select" value={currentSchema} onchange={(e) => (schemaName = (e.target as HTMLSelectElement).value)}>
              {#each data.schemas as s (s.name)}<option value={s.name}>{s.name}</option>{/each}
            </select>
          </label>
          <span class="controls">
            <button class="chip" aria-pressed={logScale} onclick={() => (logScale = !logScale)}>Log scale</button>
          </span>
        </header>
        <div class="body">
          {#if schemaInfo}
            <p class="hint mono">
              {#if schemaInfo.docs}{schemaInfo.docs} instances · {/if}{#if schemaInfo.avgDoc}{Math.round(schemaInfo.avgDoc)} bytes each on average · {/if}{#if schemaInfo.sizeKb}{schemaInfo.sizeKb} KB schema · {/if}<a href={`${BENCHMARK_REPOSITORY}/tree/main/schemas/${encodeURIComponent(schemaInfo.name)}`}>schema and instances</a>
            </p>
          {/if}
          <SchemaBars {table} schema={currentSchema} {selected} baseline={effectiveBaseline} {metric} log={logScale} {nameOf} {hrefOf} />
          <p class="hint">Bars show the median of {data.meta.runs} runs; the whisker spans the fastest and slowest run.</p>
        </div>
      </div>

      <div class="card">
        <header class="split">
          <span>Head to head</span>
          <span class="controls">
            <select class="select" aria-label="First implementation" value={a} onchange={(e) => (pickA = (e.target as HTMLSelectElement).value)}>
              {#each data.impls as i (i.id)}<option value={i.id}>{i.name}</option>{/each}
            </select>
            <span class="vs">vs</span>
            <select class="select" aria-label="Second implementation" value={b} onchange={(e) => (pickB = (e.target as HTMLSelectElement).value)}>
              {#each data.impls as i (i.id)}<option value={i.id}>{i.name}</option>{/each}
            </select>
          </span>
        </header>
        <div class="body">
          {#if h2h && h2h.points.length}
            <p class="hint">
              On {METRICS[metric].long}, <b>{nameOf(a)}</b> is {betterWord(metric)} on {h2h.aWins} of the
              {h2h.points.length} schemas both complete, and <b>{nameOf(b)}</b> on {h2h.points.length - h2h.aWins}.
              Geometric mean: {nameOf(a)} is {h2h.geomean < 1 ? `${significant(1 / h2h.geomean)}× ${betterWord(metric)}` : `${significant(h2h.geomean)}× ${worseWord(metric)}`}.
              {#if h2h.aFailed || h2h.bFailed}Left out: schemas that one of them fails ({h2h.aFailed} and {h2h.bFailed}).{/if}
            </p>
            <HeadToHeadChart result={h2h} a={nameOf(a)} b={nameOf(b)} {metric} />
          {:else}
            <div class="empty-note">These two implementations have no schema in common to compare.</div>
          {/if}
        </div>
      </div>

      <div class="card">
        <header>How to read this</header>
        <div class="body about">
          <p>
            Every figure is a total over all the instances of a schema. <b>Cold</b> is the first validation pass after
            the schema is compiled, without compilation or process start-up; <b>warm</b> is a later pass at steady
            state; <b>parse</b> is parsing every instance from memory; <b>compile</b> is preparing the schema.
            <b>Parse + warm</b> is what a service validating each request pays at steady state, and
            <b>compile + parse + cold</b> is the whole path from an uncompiled schema. <b>Peak memory</b> is the
            container’s maximum resident set size.
          </p>
          <p>
            If any run fails to validate an instance, the schema counts as failed for that implementation and is left
            out of its comparisons. The overall figure is the geometric mean of the per-schema ratios, so one large
            schema cannot dominate it, and an implementation is not penalised for the schemas it fails; check its
            coverage before reading its rank.
          </p>
          <p>
            The measurements, the schemas and the implementations’ harnesses are all in
            <a href={BENCHMARK_REPOSITORY}>sourcemeta-research/jsonschema-benchmark</a>, whose README describes the
            method. An implementation links to its Bowtie results through a <code>bowtie</code> file in its directory
            there.
          </p>
        </div>
      </div>
    </div>
  </div>
{/if}

<ChartTip />

<svelte:window onscroll={() => chartTip.hide()} />

<style>
  .doc-inner {
    max-width: 1080px;
  }
  .filters {
    display: grid;
    gap: 16px;
  }
  .filters .label {
    display: block;
    margin-bottom: 8px;
  }
  .hint {
    margin: 8px 0 0;
    font-size: var(--fs-sm);
    color: var(--text-muted);
  }
  .card .body > .hint:first-child {
    margin: 0 0 12px;
  }
  .select {
    appearance: auto;
    font-family: var(--font-mono);
    font-size: var(--fs-sm);
    color: var(--text);
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: 8px;
    padding: 5px 9px;
    max-width: 100%;
  }
  .impl-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .card > header.split {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px 14px;
  }
  /* Bowtie's pressed chip is a translucent tint, made for a card's body; in
     the grey card header it is made opaque over the surface, so it keeps the
     same colours and contrast. */
  .controls .chip[aria-pressed="true"] {
    background-color: color-mix(in srgb, var(--accent) 11%, var(--surface));
  }
  .controls {
    display: inline-flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    font-weight: 400;
  }
  .inline {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .vs {
    color: var(--text-muted);
    font-size: var(--fs-sm);
  }
  .about p {
    margin: 0 0 10px;
    color: var(--text-muted);
    max-width: 75ch;
  }
  .about b {
    color: var(--text);
    font-weight: 600;
  }
</style>
