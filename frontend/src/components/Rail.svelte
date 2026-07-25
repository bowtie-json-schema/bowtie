<script lang="ts">
  import { report } from "../stores/report.svelte";
  import { mapLanguage } from "../data/mapLanguage";
  import DialectPicker from "./DialectPicker.svelte";

  let { dialectBase }: { dialectBase?: string } = $props();

  const inScope = (language: string) =>
    report.langs.size === 0 || report.langs.has(language);
</script>

<aside class="rail">
  {#if dialectBase && report.data}
    <div class="rail-group">
      <DialectPicker current={report.data.runMetadata.dialect.shortName} base={dialectBase} />
    </div>
  {/if}

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
        <li class="impl-item {inScope(impl.language) ? '' : 'off'}">
          <a class="nm" href="#/implementations/{id}">{impl.name}</a>
          <span class="lg">{mapLanguage(impl.language)}</span>
        </li>
      {/each}
    </ul>
  </div>
</aside>
