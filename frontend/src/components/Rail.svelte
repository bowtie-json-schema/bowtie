<script lang="ts">
  import { report } from "../stores/report.svelte";
  import { mapLanguage } from "../data/mapLanguage";
  import type { Worst } from "../lib/reportModel";

  const statusDefs: {
    key: Worst | "pass";
    label: string;
    color: string;
    hint: string;
  }[] = [
    {
      key: "fail",
      label: "failed",
      color: "var(--fail)",
      hint: "The implementation ran but gave the wrong answer.",
    },
    {
      key: "err",
      label: "errored",
      color: "var(--error)",
      hint: "The implementation crashed trying to answer.",
    },
    {
      key: "skip",
      label: "skipped",
      color: "var(--skip)",
      hint: "The implementation skipped the test, usually a known bug.",
    },
    {
      key: "pass",
      label: "passing",
      color: "var(--pass)",
      hint: "The implementation gave the correct answer.",
    },
  ];

  function statusPressed(key: Worst | "pass"): boolean {
    return key === "pass" ? report.showPassing : report.statuses.has(key);
  }

  function toggleStatus(key: Worst | "pass") {
    if (key === "pass") report.showPassing = !report.showPassing;
    else report.toggleStatus(key);
  }
</script>

<aside class="rail">
  <div class="rail-group">
    <span class="label">Search cases</span>
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
  </div>

  <div class="rail-group">
    <span class="label">Status</span>
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

  <div class="rail-group">
    <span class="label">Language</span>
    <div class="chips">
      {#each report.languages as lang (lang)}
        <button
          class="chip"
          aria-pressed={report.langs.has(lang)}
          onclick={() => report.toggleLang(lang)}
        >
          {mapLanguage(lang)}
        </button>
      {/each}
    </div>
  </div>

  <div class="rail-group">
    <div style="display:flex;align-items:baseline;justify-content:space-between">
      <span class="label">In scope</span>
      <span class="impl-count">{report.scopedImplIds.length} / {report.data?.runMetadata.implementations.size ?? 0}</span>
    </div>
    <!-- Read-out of which implementations the language filter currently
         includes; filtering itself lives on the language chips above. -->
    <ul class="impl-list">
      {#each [...(report.data?.runMetadata.implementations ?? [])] as [id, impl] (id)}
        <li class="impl-item {report.langs.has(impl.language) ? '' : 'off'}">
          <span class="nm">{impl.name}</span>
          <span class="lg">{mapLanguage(impl.language)}</span>
        </li>
      {/each}
    </ul>
  </div>
</aside>
