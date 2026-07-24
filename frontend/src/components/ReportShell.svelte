<script lang="ts">
  import { report } from "../stores/report.svelte";
  import Rail from "./Rail.svelte";
  import Overview from "./Overview.svelte";
  import CaseList from "./CaseList.svelte";
  import CaseDetail from "./CaseDetail.svelte";

  // Only the live dialect report offers a dialect switcher; a local upload has
  // no dialect to navigate to.
  let { dialectBase }: { dialectBase?: string } = $props();

  // Arrow-key navigation through the currently-visible case list.
  function onKeydown(e: KeyboardEvent) {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    if ((e.target as HTMLElement)?.tagName === "INPUT") return;
    const ids = [
      ...report.failingSeqs,
      ...(report.showPassing ? report.passingSeqs : []),
    ];
    if (!ids.length) return;
    e.preventDefault();
    let idx = ids.indexOf(report.selectedSeq ?? -1);
    idx =
      e.key === "ArrowDown"
        ? Math.min(ids.length - 1, idx + 1)
        : Math.max(0, idx - 1);
    report.select(ids[idx]);
  }
</script>

<svelte:window onkeydown={onKeydown} />

<div class="shell">
  <Rail {dialectBase} />
  <main class="center">
    {#key report.selectedSeq}
      <div class="center-inner fade">
        {#if report.selectedSeq === null}
          <Overview />
        {:else}
          <CaseDetail />
        {/if}
      </div>
    {/key}
  </main>
  <CaseList />
</div>
