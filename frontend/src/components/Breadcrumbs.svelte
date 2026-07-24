<script lang="ts">
  import { router, matchRoute } from "../stores/router.svelte";
  import { SECTIONS, type Section } from "../lib/nav";
  import { report } from "../stores/report.svelte";

  const route = $derived(matchRoute(router.path));

  interface Crumb {
    label: string;
    href?: string;
    /** the compliance root: clicking it deselects the case (store state) rather than navigating */
    clears?: boolean;
  }

  // The leaf is the drill-down context (an implementation, or a selected case);
  // top-level pages have none, so no breadcrumb is shown — the top nav suffices.
  function leafLabel(): string | null {
    if (route.name === "implementation") return route.params.id ?? null;
    if (route.name === "dialect" && report.selectedSeq !== null) {
      return (
        report.data?.cases.get(report.selectedSeq)?.description ??
        `case ${report.selectedSeq}`
      );
    }
    return null;
  }

  const trail = $derived.by<Crumb[]>(() => {
    const leaf = leafLabel();
    if (!leaf) return [];

    const chain: Section[] = [];
    let cur: Section | undefined = SECTIONS[route.name];
    while (cur) {
      chain.unshift(cur);
      cur = cur.parent ? SECTIONS[cur.parent] : undefined;
    }
    return [
      ...chain.map((s) => ({ label: s.label, href: s.href, clears: s.name === "dialect" })),
      { label: leaf },
    ];
  });

  function clearSelection(e: MouseEvent) {
    e.preventDefault();
    report.selectedSeq = null;
  }
</script>

{#if trail.length}
  <nav class="crumbs" aria-label="Breadcrumb">
    {#each trail as c, i (i)}
      {#if i > 0}<span class="sep">/</span>{/if}
      {#if i === trail.length - 1}
        <span aria-current="page">{c.label}</span>
      {:else if c.clears}
        <a href={c.href} onclick={clearSelection}>{c.label}</a>
      {:else}
        <a href={c.href}>{c.label}</a>
      {/if}
    {/each}
  </nav>
{/if}
