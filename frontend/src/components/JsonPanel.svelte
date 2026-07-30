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
  <!-- a scrollable code block must be keyboard-focusable so it can be scrolled
       (axe scrollable-region-focusable); Svelte's heuristic doesn't allow for that -->
  <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
  <pre class="code" tabindex="0" role="group" aria-label="{label} JSON">{#each tokenizeJson(value) as tok, i (i)}{#if tok.cls}<span class={tok.cls}>{tok.text}</span>{:else}{tok.text}{/if}{/each}</pre>
</div>
