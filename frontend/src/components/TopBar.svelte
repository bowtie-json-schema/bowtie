<script lang="ts">
  import { theme } from "../stores/theme.svelte";
  import { router, matchRoute, type Route } from "../stores/router.svelte";
  import { report } from "../stores/report.svelte";
  import { NAV } from "../lib/nav";

  const route = $derived(matchRoute(router.path));
  const isActive = (m: Route["name"][]) => m.includes(route.name);
</script>

<header class="topbar">
  <a class="brand" href="#/" aria-label="Bowtie home">
    <span class="mark">&gt;·&lt;</span> Bowtie
  </a>

  <nav class="topnav" aria-label="Primary">
    {#each NAV as item (item.label)}
      <a
        class="navlink"
        class:active={isActive(item.match)}
        href={item.href}
        aria-current={isActive(item.match) ? "page" : undefined}
      >{item.label}</a>
    {/each}
  </nav>

  <div class="spacer"></div>

  <button
    class="ghost"
    onclick={() => theme.toggle()}
    aria-label={theme.dark ? "Switch to light theme" : "Switch to dark theme"}
    title="Toggle theme"
  >
    {#if theme.dark}
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z" />
      </svg>
    {:else}
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </svg>
    {/if}
  </button>

  <a class="ghost" href="https://docs.bowtie.report/" target="_blank" rel="noopener noreferrer">
    Docs
  </a>

  {#if report.data?.runMetadata.bowtieVersion}
    <a
      class="ver"
      href="https://github.com/bowtie-json-schema/bowtie/"
      target="_blank"
      rel="noopener noreferrer"
    >
      v{report.data.runMetadata.bowtieVersion}
    </a>
  {/if}
</header>
