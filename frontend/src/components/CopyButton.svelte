<script lang="ts">
  let {
    text,
    label = "Copy",
  }: { text: string; label?: string } = $props();

  let copied = $state(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      copied = true;
      setTimeout(() => (copied = false), 1400);
    } catch {
      // clipboard unavailable (non-secure context); nothing to do
    }
  }
</script>

<button
  class="copy-btn"
  class:copied
  onclick={copy}
  aria-label={copied ? "Copied" : label}
  title={copied ? "Copied" : label}
>
  {#if copied}
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M20 6 9 17l-5-5" /></svg>
  {:else}
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15V5a2 2 0 0 1 2-2h10" /></svg>
  {/if}
</button>

<style>
  .copy-btn {
    display: inline-grid;
    place-items: center;
    width: 26px;
    height: 26px;
    border-radius: 6px;
    border: 1px solid var(--border-strong);
    background: var(--surface);
    color: var(--text-muted);
    cursor: pointer;
    transition: color 0.12s, border-color 0.12s;
  }
  .copy-btn:hover {
    color: var(--text);
    border-color: var(--text-faint);
  }
  .copy-btn.copied {
    color: var(--pass);
    border-color: color-mix(in srgb, var(--pass) 50%, transparent);
  }
</style>
