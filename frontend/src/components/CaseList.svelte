<script lang="ts">
  import { report } from "../stores/report.svelte";
  import { caseGroup } from "../lib/reportModel";

  const failing = $derived(report.failingSeqs);
  const passing = $derived(report.passingSeqs);
  const shown = $derived(failing.length + (report.showPassing ? passing.length : 0));

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
  {@const nf = report.nDisagree(seq)}
  <button
    class="case-row {report.selectedSeq === seq ? 'sel' : ''}"
    aria-current={report.selectedSeq === seq ? "true" : undefined}
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
