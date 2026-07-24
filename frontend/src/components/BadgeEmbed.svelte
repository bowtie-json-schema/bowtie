<script lang="ts">
  import type Implementation from "../data/Implementation";
  import CopyButton from "./CopyButton.svelte";

  let { implementation }: { implementation: Implementation } = $props();

  interface BadgeInfo {
    name: string;
    altText: string;
    uri: { href(): string };
  }

  const badges = $derived(implementation.badges());
  const categories = $derived(Object.entries(badges) as [string, BadgeInfo[]][]);

  const formats: { name: string; generate: (b: BadgeInfo) => string }[] = [
    { name: "URL", generate: (b) => b.uri.href() },
    { name: "Markdown", generate: (b) => `![${b.altText}](${b.uri.href()})` },
    {
      name: "reST",
      generate: (b) => `.. image:: ${b.uri.href()}\n    :alt: ${b.altText}`,
    },
    { name: "AsciiDoc", generate: (b) => `image:${b.uri.href()}[${b.altText}]` },
    {
      name: "HTML",
      generate: (b) => `<img alt="${b.altText}" src="${b.uri.href()}"/>`,
    },
  ];

  let activeName = $state<string | null>(null);
  let activeFormat = $state(formats[1]); // Markdown
  const activeBadge = $derived(
    categories.flatMap(([, list]) => list).find((b) => b.name === activeName) ??
      badges.Metadata[0],
  );
  const snippet = $derived(activeFormat.generate(activeBadge));
</script>

<div class="card">
  <header>Embeddable badges</header>
  <div class="body">
    <p class="h-lead" style="margin-bottom:16px">
      Bowtie rebuilds these badges for <code>{implementation.name}</code> as it
      re-runs its report, so an embedded badge stays up to date on its own.
    </p>

    <div class="badge-embed">
      <div class="be-badges">
        {#each categories as [category, list] (category)}
          <div class="be-cat">
            <span class="label">{category}</span>
            {#each list as badge (badge.name)}
              <button
                class="be-item"
                class:active={badge.name === activeBadge.name}
                onclick={() => (activeName = badge.name)}
              >{badge.name}</button>
            {/each}
          </div>
        {/each}
      </div>

      <div class="be-main">
        <div class="be-formats">
          {#each formats as format (format.name)}
            <button
              class="be-format"
              class:active={format.name === activeFormat.name}
              onclick={() => (activeFormat = format)}
            >{format.name}</button>
          {/each}
        </div>

        <div class="be-snippet">
          <pre>{snippet}</pre>
          <span class="be-copy"><CopyButton text={snippet} label="Copy snippet" /></span>
        </div>

        <img class="be-preview" alt={activeBadge.altText} src={activeBadge.uri.href()} />
      </div>
    </div>
  </div>
</div>

<style>
  .badge-embed {
    display: grid;
    grid-template-columns: minmax(150px, 220px) 1fr;
    gap: 22px;
  }
  .be-cat {
    margin-bottom: 14px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .be-cat .label {
    margin-bottom: 4px;
  }
  .be-item,
  .be-format {
    text-align: left;
    border: 0;
    background: transparent;
    color: var(--text-muted);
    font-size: 12.5px;
    padding: 5px 9px;
    border-radius: 6px;
    cursor: pointer;
  }
  .be-item:hover,
  .be-format:hover {
    background: var(--surface-2);
    color: var(--text);
  }
  .be-item.active,
  .be-format.active {
    background: var(--sel-bg);
    color: var(--accent);
  }
  .be-formats {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 12px;
  }
  .be-format {
    font-family: var(--font-mono);
    font-size: 11.5px;
    border: 1px solid var(--border);
  }
  .be-snippet {
    position: relative;
    border: 1px solid var(--border);
    border-radius: 9px;
    background: var(--surface-2);
    overflow: hidden;
  }
  .be-snippet pre {
    margin: 0;
    padding: 13px 44px 13px 14px;
    overflow-x: auto;
    font-family: var(--font-mono);
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
    color: var(--text);
  }
  .be-copy {
    position: absolute;
    top: 8px;
    right: 8px;
  }
  .be-preview {
    display: block;
    margin-top: 18px;
    max-width: 100%;
  }
  @media (max-width: 640px) {
    .badge-embed {
      grid-template-columns: 1fr;
    }
  }
</style>
