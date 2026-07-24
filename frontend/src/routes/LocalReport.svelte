<script lang="ts">
  import { report } from "../stores/report.svelte";
  import { parseReportData } from "../data/parseReportData";
  import ReportShell from "../components/ReportShell.svelte";

  let loaded = $state(false);
  let dragActive = $state(false);
  let invalid = $state(false);
  let fileInput: HTMLInputElement | undefined = $state();

  function handleFile(file: File) {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = String(e.target?.result ?? "");
        const lines = text
          .trim()
          .split(/\r?\n/)
          .map((l) => JSON.parse(l) as Record<string, unknown>);
        report.load(parseReportData(lines));
        document.title = "Bowtie – local report";
        loaded = true;
      } catch {
        invalid = true;
        setTimeout(() => (invalid = false), 4000);
      }
    };
    reader.readAsText(file);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    dragActive = false;
    const file = e.dataTransfer?.files?.[0];
    if (file) handleFile(file);
  }

  function onChange(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) handleFile(file);
  }

  function pick() {
    if (fileInput) fileInput.value = "";
    fileInput?.click();
  }
</script>

{#if loaded}
  <ReportShell />
{:else}
  <div class="doc">
    <div class="doc-inner">
      <h1 class="page">Upload a report</h1>
      <p class="h-lead">
        Explore a report you generated locally with Bowtie’s CLI — it’s parsed
        in your browser and never leaves your machine.
      </p>

      <div
        class="dropzone {dragActive ? 'active' : ''} {invalid ? 'invalid' : ''}"
        role="button"
        tabindex="0"
        aria-label="Choose or drop a Bowtie report file"
        ondragenter={(e) => {
          e.preventDefault();
          dragActive = true;
        }}
        ondragover={(e) => {
          e.preventDefault();
          dragActive = true;
        }}
        ondragleave={(e) => {
          e.preventDefault();
          dragActive = false;
        }}
        ondrop={onDrop}
        onclick={pick}
        onkeydown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            pick();
          }
        }}
      >
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
          <path d="M12 15V3m0 0 4 4m-4-4L8 7" />
          <path d="M20 16.5A4.5 4.5 0 0 0 17.5 8h-1.3A7 7 0 1 0 4 14.9" />
        </svg>
        {#if invalid}
          <p style="color:var(--fail);font-weight:560;margin:0">
            That doesn’t look like a Bowtie report.
          </p>
        {:else}
          <p style="margin:0">Drag &amp; drop a JSON report here, or click to choose a file.</p>
        {/if}
      </div>

      <input
        bind:this={fileInput}
        type="file"
        accept=".json,application/json"
        onchange={onChange}
        hidden
      />

      <p class="h-lead" style="margin-top:20px">
        Generate one with e.g.
        <code>bowtie suite -i lua-jsonschema &lt;test-file&gt; &gt; report.json</code>
        — see <a href="https://docs.bowtie.report/en/stable/cli/">the CLI docs</a>.
      </p>
    </div>
  </div>
{/if}
