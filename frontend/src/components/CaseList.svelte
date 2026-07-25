<script lang="ts">
  import { report } from "../stores/report.svelte";
  import { caseGroup, type Worst } from "../lib/reportModel";

  const failing = $derived(report.failingSeqs);
  const passing = $derived(report.passingSeqs);
  const shown = $derived(failing.length + (report.showPassing ? passing.length : 0));

  const statusDefs: {
    key: Worst | "pass";
    label: string;
    color: string;
    hint: string;
  }[] = [
    { key: "fail", label: "failed", color: "var(--fail)", hint: "The implementation ran but gave the wrong answer." },
    { key: "err", label: "errored", color: "var(--error)", hint: "The implementation crashed trying to answer." },
    { key: "skip", label: "skipped", color: "var(--skip)", hint: "The implementation skipped the test, usually a known bug." },
    { key: "pass", label: "passing", color: "var(--pass)", hint: "The implementation gave the correct answer." },
  ];

  function statusPressed(key: Worst | "pass"): boolean {
    return key === "pass" ? report.showPassing : report.statuses.has(key);
  }

  function toggleStatus(key: Worst | "pass") {
    if (key === "pass") report.showPassing = !report.showPassing;
    else report.toggleStatus(key);
  }

  function seg(n: number, total: number, cls: string) {
    if (!n) return null;
    return { width: (n / total) * 100, cls };
  }

  function segments(seq: number) {
    const n = report.countsWorst(seq);
    const total = report.scopedImplIds.length || 1;
    return [
      seg(n.ok, total, "ok"),
      seg(n.fail, total, "fail"),
      seg(n.err, total, "err"),
      seg(n.skip, total, "skip"),
    ].filter((s): s is { width: number; cls: string } => s !== null);
  }
</script>

<aside class="master">
  <div class="master-head">
    <div class="row1">
      <h2>Test cases</h2>
      <span class="n">{shown} shown</span>
    </div>
    <div class="master-filters">
      <div class="search">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="7" /><path d="m21 21-4-4" />
        </svg>
        <input
          type="text"
          placeholder="description, keyword…"
          aria-label="Search test cases"
          bind:value={report.search}
        />
      </div>
      <div class="chips">
        {#each statusDefs as s (s.key)}
          <button
            class="chip status"
            aria-pressed={statusPressed(s.key)}
            title={s.hint}
            onclick={() => toggleStatus(s.key)}
          >
            <span class="dot" style="background:{s.color}"></span>{s.label}
          </button>
        {/each}
      </div>
    </div>
  </div>

  <div class="section-label"><span class="label">Failing · {failing.length}</span></div>
  {#if failing.length === 0}
    <div class="empty-note">No failing cases match these filters.</div>
  {/if}
  {#each failing as seq (seq)}
    {@render caseRow(seq)}
  {/each}

  <button
    class="passing-toggle"
    aria-expanded={report.showPassing}
    onclick={() => (report.showPassing = !report.showPassing)}
  >
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <path d="m9 6 6 6-6 6" />
    </svg>
    Passing everywhere
    <span class="n">{passing.length}</span>
  </button>
  {#if report.showPassing}
    {#each passing as seq (seq)}
      {@render caseRow(seq)}
    {/each}
  {/if}
</aside>

{#snippet caseRow(seq: number)}
  {@const c = report.data!.cases.get(seq)!}
  {@const group = caseGroup(c)}
  {@const n = report.countsWorst(seq)}
  {@const nf = n.fail + n.err + n.skip}
  <button
    class="case-row {report.selectedSeq === seq ? 'sel' : ''}"
    aria-current={report.selectedSeq === seq ? "true" : undefined}
    title={nf ? `${n.fail} failed · ${n.err} errored · ${n.skip} skipped` : undefined}
    onclick={() => report.select(seq)}
  >
    <div class="cr-top">
      {#if group}<span class="grp">{group}</span>{/if}
      {#if nf}<span class="nfail">{nf} disagree</span>{/if}
    </div>
    <div class="desc">{c.description}</div>
    <div class="pbar">
      {#each segments(seq) as s (s.cls)}
        <i class={s.cls} style="width:{s.width}%{s.cls !== 'ok' ? ';min-width:4px' : ''}"></i>
      {/each}
    </div>
  </button>
{/snippet}
