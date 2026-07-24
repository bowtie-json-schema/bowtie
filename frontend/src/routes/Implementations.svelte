<script lang="ts">
  import Implementation from "../data/Implementation";
  import { mapLanguage } from "../data/mapLanguage";
  import Spinner from "../components/Spinner.svelte";

  let impls = $state<Implementation[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

  $effect(() => {
    document.title = "Bowtie – implementations";
    void (async () => {
      try {
        const all = await Implementation.fetchAllImplementationsData();
        impls = [...all.values()];
      } catch (e) {
        error = e instanceof Error ? e.message : String(e);
      } finally {
        loading = false;
      }
    })();
  });

  const byLanguage = $derived.by(() => {
    const out: Record<string, Implementation[]> = {};
    for (const i of impls) (out[i.language] ??= []).push(i);
    for (const list of Object.values(out)) {
      list.sort((a, b) => a.name.localeCompare(b.name));
    }
    return out;
  });
  const languages = $derived(Object.keys(byLanguage).sort());
</script>

{#if loading}
  <Spinner />
{:else if error}
  <div class="doc"><div class="doc-inner">
    <h1 class="page">Implementations</h1>
    <div class="empty-note">Couldn't load implementations.<br />{error}</div>
  </div></div>
{:else}
  <div class="doc">
    <div class="doc-inner">
      <h1 class="page">Implementations</h1>
      <p class="h-lead">
        Every JSON Schema implementation Bowtie tracks ({impls.length}). Open one
        to see its compliance, badges, and all of its failing tests.
      </p>
      {#each languages as lang (lang)}
        <div class="impl-group">
          <span class="label">{mapLanguage(lang)}</span>
          <div class="impl-grid">
            {#each byLanguage[lang] as impl (impl.id)}
              <a class="impl-card" href="#{impl.routePath}">
                <span class="ic-name">{impl.name}</span>
                {#if impl.version}<span class="ic-ver mono">{impl.version}</span>{/if}
              </a>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}

<style>
  .impl-group {
    margin-bottom: 22px;
  }
  .impl-group .label {
    display: block;
    margin-bottom: 8px;
  }
  .impl-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    gap: 8px;
  }
  .impl-card {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 8px;
    padding: 10px 13px;
    border: 1px solid var(--border);
    border-radius: 9px;
    background: var(--surface);
    text-decoration: none;
    color: var(--text);
  }
  .impl-card:hover {
    border-color: var(--accent);
    text-decoration: none;
  }
  .ic-name {
    font-size: 13px;
    font-weight: 520;
    flex: 1 1 auto;
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .ic-ver {
    font-size: 10.5px;
    color: var(--text-faint);
    flex: 0 1 auto;
    min-width: 0;
    max-width: 45%;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
</style>
