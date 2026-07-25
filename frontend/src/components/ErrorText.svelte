<script lang="ts">
  // Error output (stack traces, stderr dumps) can be pathologically large —
  // some reports carry tens of megabytes in a single result. Rendering that
  // verbatim hangs the browser (issue #2723), so show a bounded slice and
  // offer the full text as a raw plain-text tab, generated on demand.
  let { text }: { text: string } = $props();

  // A real stack trace is a few KB and renders instantly, so show up to ~10k
  // in full; truncation only exists to tame the pathological megabyte dumps.
  const DISPLAY = 10000; // characters shown before truncating
  const INLINE_MAX = 100000; // above this, only the raw tab is offered (no inline "Show all")

  const isLong = $derived(text.length > DISPLAY);
  let expanded = $state(false);
  const shown = $derived(!isLong || expanded ? text : text.slice(0, DISPLAY));

  const fmt = (n: number) => n.toLocaleString();

  function openRaw() {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener");
    // give the new tab time to load before releasing the object URL
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }
</script>

<span class="et-body">{shown}{#if isLong && !expanded}…{/if}</span>
{#if isLong}
  <div class="et-controls">
    <span class="et-note">
      {#if expanded}showing all {fmt(text.length)} characters{:else}truncated · {fmt(DISPLAY)} of {fmt(text.length)} characters{/if}
    </span>
    {#if !expanded && text.length <= INLINE_MAX}
      <button type="button" class="et-btn" onclick={() => (expanded = true)}>Show all</button>
    {/if}
    <button type="button" class="et-btn" onclick={openRaw}>Open raw&nbsp;↗</button>
  </div>
{/if}

<style>
  .et-body {
    display: block;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .et-controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    margin-top: 8px;
  }
  .et-note {
    font-family: var(--font-sans);
    font-size: var(--fs-2xs);
    color: var(--text-faint);
  }
  .et-btn {
    font-family: var(--font-sans);
    font-size: var(--fs-2xs);
    border: 1px solid var(--border-strong);
    background: var(--surface);
    color: var(--text-muted);
    border-radius: 6px;
    padding: 2px 8px;
    cursor: pointer;
  }
  .et-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
</style>
