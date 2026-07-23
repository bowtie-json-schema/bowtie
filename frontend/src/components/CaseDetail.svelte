<script lang="ts">
  import { report } from "../stores/report.svelte";
  import { mapLanguage } from "../data/mapLanguage";
  import { tokenizeJson } from "../lib/highlightJson";
  import {
    resultFor,
    stateToWorst,
    testCounts,
    caseGroup,
    type Worst,
  } from "../lib/reportModel";

  const data = $derived(report.data!);
  const seq = $derived(report.selectedSeq!);
  const c = $derived(data.cases.get(seq)!);
  const t = $derived(Math.min(report.selectedTest, c.tests.length - 1));
  const implIds = $derived(report.scopedImplIds);
  const group = $derived(caseGroup(c));

  const nDisagree = $derived(report.nDisagree(seq));

  const implName = (id: string) => data.runMetadata.implementations.get(id)!.name;
  const implLang = (id: string) => data.runMetadata.implementations.get(id)!.language;

  const counts = $derived(testCounts(data, implIds, seq, t));

  const groups = $derived.by(() => {
    const defs: { state: Worst; label: string }[] = [
      { state: "fail", label: "failed" },
      { state: "err", label: "errored" },
      { state: "skip", label: "skipped" },
    ];
    return defs
      .map(({ state, label }) => ({
        state,
        label,
        members: implIds.filter(
          (id) => stateToWorst(resultFor(data, id, seq, t).state) === state,
        ),
      }))
      .filter((g) => g.members.length > 0);
  });

  function diagMessage(id: string): string {
    const r = resultFor(data, id, seq, t);
    if (r.message) return r.message;
    if (r.state === "failed") {
      return c.tests[t].valid ? "unexpectedly invalid" : "unexpectedly valid";
    }
    return "";
  }

  function toggleDiag(id: string) {
    report.openDiag = report.openDiag === id ? null : id;
  }
</script>

<div class="crumbs">
  <a href="#/" onclick={(e) => { e.preventDefault(); report.selectedSeq = null; }}>Report</a>
  {#if group}<span class="sep">/</span><span class="mono" style="color:var(--accent)">{group}</span>{/if}
</div>

<h1 class="page">{c.description}</h1>

<div class="case-meta">
  <span class="tag"><b>{c.tests.length}</b> tests</span>
  <span class="tag"><b style="color:var(--fail)">{nDisagree}</b> of {implIds.length} impls disagree</span>
  {#if c.comment}<span class="tag">has comment</span>{/if}
</div>

<div class="split">
  <div class="panel">
    <header><span class="label">Schema</span><span class="hint">the whole case</span></header>
    <pre class="code">{#each tokenizeJson(c.schema) as tok, i (i)}{#if tok.cls}<span class={tok.cls}>{tok.text}</span>{:else}{tok.text}{/if}{/each}</pre>
  </div>
  <div class="panel">
    <header>
      <span class="label">Instance</span>
      <span class="hint">test {t + 1} of {c.tests.length}</span>
    </header>
    <pre class="code">{#each tokenizeJson(c.tests[t].instance) as tok, i (i)}{#if tok.cls}<span class={tok.cls}>{tok.text}</span>{:else}{tok.text}{/if}{/each}</pre>
  </div>
</div>

<span class="label sec-label">Tests · pick one to inspect</span>
<div class="tlist">
  {#each c.tests as test, ti (ti)}
    {@const n = testCounts(data, implIds, seq, ti)}
    <button class="tline {ti === t ? 'sel' : ''}" onclick={() => report.selectTest(ti)}>
      <span class="d">{test.description}</span>
      <span class="exp">expect {test.valid ? "valid" : "invalid"}</span>
      <span class="tally">
        <span class={n.ok ? "t-ok" : "t-ok mut"}>{n.ok} ✓</span>
        <span class={n.fail ? "t-fail" : "t-fail mut"}>{n.fail} ✗</span>
        <span class={n.err ? "t-err" : "t-err mut"}>{n.err} !</span>
        <span class={n.skip ? "t-skip" : "t-skip mut"}>{n.skip} –</span>
      </span>
    </button>
  {/each}
</div>

<div class="dis">
  <div class="dhead">
    <span class="for">Results for <b>“{c.tests[t].description}”</b></span>
    <span class="dsum">
      <span class="d-ok">{counts.ok} ✓</span>
      {#if counts.fail}<span class="d-fail">{counts.fail} ✗</span>{/if}
      {#if counts.err}<span class="d-err">{counts.err} !</span>{/if}
      {#if counts.skip}<span class="d-skip">{counts.skip} –</span>{/if}
    </span>
  </div>

  {#if groups.length === 0}
    <div class="passed-line">
      <span class="tick">✓</span> Every in-scope implementation gets this test right.
    </div>
  {:else}
    {#each groups as g (g.state)}
      <div class="ogroup">
        <div class="oh">
          <span class="badge {g.state}">{g.label} · {g.members.length}</span>
        </div>
        <div class="chips-impl">
          {#each g.members as id (id)}
            <button
              class="ichip {report.openDiag === id ? 'open' : ''}"
              onclick={() => toggleDiag(id)}
            >
              {implName(id)}<span class="il">{mapLanguage(implLang(id))}</span>
            </button>
          {/each}
        </div>
        {#if g.members.includes(report.openDiag ?? "")}
          <div class="diag">
            <span class="who">{implName(report.openDiag!)} · {mapLanguage(implLang(report.openDiag!))}</span>{diagMessage(report.openDiag!) || "(no message reported)"}
          </div>
        {/if}
      </div>
    {/each}
    <div class="passed-line">
      <span class="tick">✓</span>
      {counts.ok} of {implIds.length} implementations agree on this test.
    </div>
  {/if}
</div>
