<script lang="ts">
  import Implementation from "../data/Implementation";
  import { mapLanguage } from "../data/mapLanguage";
  import Spinner from "../components/Spinner.svelte";

  let { id }: { id: string } = $props();

  let impl = $state<Implementation | null>(null);
  let loading = $state(true);
  let notFound = $state(false);

  async function load(implId: string) {
    loading = true;
    notFound = false;
    await Implementation.fetchAllImplementationsData();
    const found = Implementation.withId(implId);
    if (!found) {
      notFound = true;
    } else {
      impl = found;
      document.title = `Bowtie – ${found.name}`;
    }
    loading = false;
  }

  $effect(() => {
    void load(id);
  });
</script>

{#if loading}
  <Spinner />
{:else if notFound || !impl}
  <div class="doc">
    <div class="doc-inner">
      <h1 class="page">Unknown implementation</h1>
      <p class="h-lead">No implementation with id <code>{id}</code>. <a href="#/">Back to the report</a>.</p>
    </div>
  </div>
{:else}
  <div class="doc">
    <div class="doc-inner">
      <div class="crumbs">
        <a href="#/">Report</a><span class="sep">/</span>
        <span class="mono" style="color:var(--accent)">{impl.id}</span>
      </div>
      <h1 class="page">{impl.name}</h1>
      <p class="h-lead">
        {mapLanguage(impl.language)}{#if impl.language_version} · {impl.language_version}{/if}
        {#if impl.version} · v{impl.version}{/if}
      </p>

      <div class="card">
        <header>Details</header>
        <div class="body">
          <table style="width:100%;border-collapse:collapse;font-size:13px">
            <tbody>
              <tr><td class="label" style="padding:6px 12px 6px 0;width:150px">Homepage</td><td><a href={impl.homepage}>{impl.homepage}</a></td></tr>
              {#if impl.documentation}
                <tr><td class="label" style="padding:6px 12px 6px 0">Docs</td><td><a href={impl.documentation}>{impl.documentation}</a></td></tr>
              {/if}
              <tr><td class="label" style="padding:6px 12px 6px 0">Source</td><td><a href={impl.source}>{impl.source}</a></td></tr>
              <tr><td class="label" style="padding:6px 12px 6px 0">Issues</td><td><a href={impl.issues}>{impl.issues}</a></td></tr>
              <tr><td class="label" style="padding:6px 12px 6px 0">Language</td><td>{mapLanguage(impl.language)}{#if impl.language_version} <span style="color:var(--text-muted)">({impl.language_version})</span>{/if}</td></tr>
              {#if impl.os}
                <tr><td class="label" style="padding:6px 12px 6px 0">OS</td><td>{impl.os}{#if impl.os_version} <span style="color:var(--text-muted)">({impl.os_version})</span>{/if}</td></tr>
              {/if}
            </tbody>
          </table>
        </div>
      </div>

      <p class="h-lead">
        Compliance table, badges, and the versions trend chart are still to be
        ported to the new layout.
      </p>
    </div>
  </div>
{/if}
