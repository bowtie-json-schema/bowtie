<script lang="ts">
  import { router, matchRoute } from "./stores/router.svelte";
  import TopBar from "./components/TopBar.svelte";
  import DialectReport from "./routes/DialectReport.svelte";
  import Benchmarks from "./routes/Benchmarks.svelte";
  import ImplementationReport from "./routes/ImplementationReport.svelte";
  import LocalReport from "./routes/LocalReport.svelte";
  import NotFound from "./routes/NotFound.svelte";

  const route = $derived(matchRoute(router.path));
</script>

<div class="app">
  <TopBar />
  <div class="route">
    {#if route.name === "dialect"}
      <DialectReport draftName={route.params.draftName} />
    {:else if route.name === "benchmarks"}
      <Benchmarks draftName={route.params.draftName} />
    {:else if route.name === "implementation"}
      <ImplementationReport id={route.params.id ?? ""} />
    {:else if route.name === "local"}
      <LocalReport />
    {:else}
      <NotFound />
    {/if}
  </div>
</div>
