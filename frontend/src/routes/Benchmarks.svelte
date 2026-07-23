<script lang="ts">
  let { draftName }: { draftName?: string } = $props();
</script>

<div class="doc">
  <div class="doc-inner">
    <h1 class="page">Benchmarks</h1>
    <p class="h-lead">
      The benchmarks view hasn't been ported to the new layout yet{#if draftName}
        ({draftName}){/if}. Coming in a later phase of the Svelte rewrite.
    </p>
    <p><a href="#/">Back to the dialect report</a></p>
  </div>
</div>
