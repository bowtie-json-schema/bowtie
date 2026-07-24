<script lang="ts">
  import Dialect from "../data/Dialect";
  import Implementation from "../data/Implementation";
  import { report } from "../stores/report.svelte";
  import { router } from "../stores/router.svelte";
  import ReportShell from "../components/ReportShell.svelte";
  import Spinner from "../components/Spinner.svelte";

  let { draftName }: { draftName?: string } = $props();

  let loading = $state(true);
  let error = $state<string | null>(null);
  let loadToken = 0;

  async function load(name?: string) {
    const token = ++loadToken;
    loading = true;
    error = null;
    try {
      const dialect = name ? Dialect.withName(name) : Dialect.latest();
      document.title = `Bowtie – ${dialect.prettyName}`;
      const [data, allImpls] = await Promise.all([
        dialect.fetchReport(),
        Implementation.fetchAllImplementationsData(),
      ]);
      if (token !== loadToken) return; // a newer navigation superseded this one
      report.load(data, allImpls);
      report.applyQuery(router.query); // restore filters/selection from the URL
    } catch (e) {
      if (token === loadToken) error = e instanceof Error ? e.message : String(e);
    } finally {
      if (token === loadToken) loading = false;
    }
  }

  $effect(() => {
    void load(draftName);
  });

  // Mirror the shareable state back into the URL (no history spam, no reload).
  $effect(() => {
    if (loading || error) return;
    const q = report.toQuery();
    const path = draftName ? `/dialects/${draftName}` : "/";
    const newHash = q ? `#${path}?${q}` : `#${path}`;
    if (location.hash !== newHash) {
      history.replaceState(history.state, "", newHash);
    }
  });
</script>

{#if loading}
  <Spinner />
{:else if error}
  <div class="empty-note">Couldn't load this report.<br />{error}</div>
{:else}
  <ReportShell />
{/if}
