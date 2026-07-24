<script lang="ts">
  import { tokenizeJson } from "../lib/highlightJson";
  import CopyButton from "./CopyButton.svelte";

  let {
    label,
    value,
    hint,
  }: { label: string; value: unknown; hint?: string } = $props();

  const json = $derived(JSON.stringify(value, null, 2) ?? "");
</script>

<div class="panel">
  <header>
    <span class="label">{label}</span>
    <span class="hdr-right">
      {#if hint}<span class="hint">{hint}</span>{/if}
      <CopyButton text={json} label="Copy {label.toLowerCase()}" />
    </span>
  </header>
  <pre class="code">{#each tokenizeJson(value) as tok, i (i)}{#if tok.cls}<span class={tok.cls}>{tok.text}</span>{:else}{tok.text}{/if}{/each}</pre>
</div>
