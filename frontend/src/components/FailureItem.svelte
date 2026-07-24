<script lang="ts">
  import type { Failure } from "../lib/reportModel";
  import JsonPanel from "./JsonPanel.svelte";

  let { failure }: { failure: Failure } = $props();

  let open = $state(false);
  const stateClass = { failed: "fail", errored: "err", skipped: "skip" } as const;
</script>

<details class="failure" bind:open>
  <summary>
    <span class="badge {stateClass[failure.state]}">{failure.state}</span>
    <span class="f-text">
      <span class="f-case">{failure.caseDescription}</span>
      <span class="f-test">{failure.testDescription}</span>
    </span>
  </summary>
  {#if open}
    <div class="f-body">
      {#if failure.message}<pre class="f-msg">{failure.message}</pre>{/if}
      <div class="split">
        <JsonPanel label="Schema" value={failure.schema} />
        <JsonPanel label="Instance" value={failure.instance} />
      </div>
    </div>
  {/if}
</details>

<style>
  .failure {
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--surface);
    margin-bottom: 8px;
    overflow: hidden;
  }
  summary {
    list-style: none;
    cursor: pointer;
    padding: 10px 13px;
    display: flex;
    align-items: baseline;
    gap: 11px;
  }
  summary::-webkit-details-marker {
    display: none;
  }
  .badge {
    flex: none;
    font-family: var(--font-mono);
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 5px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .badge.fail { background: color-mix(in srgb, var(--fail) 16%, transparent); color: var(--fail); }
  .badge.err { background: color-mix(in srgb, var(--error) 18%, transparent); color: var(--error); }
  .badge.skip { background: color-mix(in srgb, var(--skip) 16%, transparent); color: var(--skip); }
  .f-text {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }
  .f-case {
    font-size: 13px;
    font-weight: 520;
  }
  .f-test {
    font-size: 12px;
    color: var(--text-muted);
  }
  .f-body {
    padding: 4px 13px 14px;
    border-top: 1px solid var(--border);
  }
  .f-msg {
    margin: 12px 0;
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--surface-2);
    font-family: var(--font-mono);
    font-size: 11.5px;
    line-height: 1.55;
    color: var(--text-muted);
    white-space: pre-wrap;
    word-break: break-word;
    overflow-x: auto;
  }
</style>
