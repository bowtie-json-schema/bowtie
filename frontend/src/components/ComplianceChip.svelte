<script lang="ts">
  import type { Compliance } from "../data/compliance";

  let { compliance, dialectName }: { compliance: Compliance; dialectName: string } = $props();

  const view = $derived.by(() => {
    switch (compliance.state) {
      case "tested":
        return compliance.percent === 100
          ? { text: "100%", tone: "pass", title: `Passes every Bowtie test of ${dialectName}` }
          : { text: `${compliance.percent}%`, tone: "partial", title: `Passes ${compliance.percent}% of Bowtie's tests of ${dialectName}` };
      case "unsupported":
        return { text: `no ${dialectName}`, tone: "none", title: `Bowtie tests it, but not on ${dialectName}` };
      case "untested":
        return { text: "not in Bowtie", tone: "none", title: "Bowtie does not test this implementation" };
      default:
        return { text: "?", tone: "none", title: "Its Bowtie results could not be loaded" };
    }
  });
</script>

<span class="cchip {view.tone}" title={view.title}>{view.text}</span>

<style>
  .cchip {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: var(--fs-2xs);
    line-height: 1.6;
    padding: 0 6px;
    border-radius: 10px;
    border: 1px solid var(--border-strong);
    color: var(--text-muted);
    white-space: nowrap;
  }
  .cchip.pass {
    color: var(--pass);
    border-color: color-mix(in srgb, var(--pass) 45%, transparent);
  }
  .cchip.partial {
    color: var(--error);
    border-color: color-mix(in srgb, var(--error) 45%, transparent);
  }
</style>
