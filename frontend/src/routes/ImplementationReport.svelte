<script lang="ts">
  import Dialect from "../data/Dialect";
  import Implementation from "../data/Implementation";
  import { mapLanguage } from "../data/mapLanguage";
  import {
    prepareDialectsComplianceReportFor,
    type ReportData,
    type Totals,
  } from "../data/parseReportData";
  import VersionsTrend from "../components/VersionsTrend.svelte";
  import BadgeEmbed from "../components/BadgeEmbed.svelte";
  import ImplementationFailures from "../components/ImplementationFailures.svelte";
  import Spinner from "../components/Spinner.svelte";

  let { id, badges = false }: { id: string; badges?: boolean } = $props();

  let impl = $state<Implementation | null>(null);
  let compliance = $state<[Dialect, Partial<Totals>][]>([]);
  let reports = $state<Map<Dialect, ReportData> | null>(null);
  let loading = $state(true);
  let notFound = $state(false);
  let showBadges = $state(false);

  $effect(() => {
    if (badges) showBadges = true;
  });

  const badTotal = (t: Partial<Totals>) =>
    (t.failedTests ?? 0) + (t.erroredTests ?? 0) + (t.skippedTests ?? 0);

  async function load(implId: string) {
    loading = true;
    notFound = false;
    document.title = `Bowtie – ${implId}`;
    const [, allReports] = await Promise.all([
      Implementation.fetchAllImplementationsData(),
      Dialect.fetchAllReports(),
    ]);
    const found = Implementation.withId(implId);
    if (!found) {
      notFound = true;
      loading = false;
      return;
    }
    impl = found;
    reports = allReports;
    document.title = `Bowtie – ${found.name}`;
    compliance = [
      ...prepareDialectsComplianceReportFor(found.id, allReports).entries(),
    ].sort(
      ([da, a], [db, b]) =>
        badTotal(a) - badTotal(b) ||
        +db.firstPublicationDate - +da.firstPublicationDate,
    );
    await found.fetchVersions();
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
      <p class="h-lead">
        No implementation with id <code>{id}</code>. <a href="#/">Back to the report</a>.
      </p>
    </div>
  </div>
{:else}
  <div class="doc">
    <div class="doc-inner">
      <div class="crumbs">
        <a href="#/">Report</a><span class="sep">/</span>
        <span class="mono" style="color:var(--accent)">{impl.id}</span>
      </div>
      <div class="impl-head">
        <div>
          <h1 class="page">{impl.name}</h1>
          <p class="h-lead">
            {mapLanguage(impl.language)}{#if impl.language_version}
              · {impl.language_version}{/if}{#if impl.version} · v{impl.version}{/if}
          </p>
        </div>
        <button
          class="btn-badges"
          aria-expanded={showBadges}
          onclick={() => (showBadges = !showBadges)}
        >Badges</button>
      </div>

      {#if showBadges}
        <BadgeEmbed implementation={impl} />
      {/if}

      {#if reports}
        <ImplementationFailures {reports} implId={impl.id} implName={impl.name} />
      {/if}

      <div class="card">
        <header>Details</header>
        <div class="body">
          <table class="kv">
            <tbody>
              <tr><th>Homepage</th><td><a href={impl.homepage}>{impl.homepage}</a></td></tr>
              {#if impl.documentation}
                <tr><th>Docs</th><td><a href={impl.documentation}>{impl.documentation}</a></td></tr>
              {/if}
              <tr><th>Source</th><td><a href={impl.source}>{impl.source}</a></td></tr>
              <tr><th>Issues</th><td><a href={impl.issues}>{impl.issues}</a></td></tr>
              <tr>
                <th>Language</th>
                <td>{mapLanguage(impl.language)}{#if impl.language_version} <span class="muted">({impl.language_version})</span>{/if}</td>
              </tr>
              {#if impl.os}
                <tr><th>OS</th><td>{impl.os}{#if impl.os_version} <span class="muted">({impl.os_version})</span>{/if}</td></tr>
              {/if}
              <tr>
                <th>Supported dialects</th>
                <td><img class="badge" alt="Supported dialects" src={impl.versionsBadge().href()} /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <header>Compliance</header>
        <div class="body" style="overflow-x:auto">
          <table class="compliance">
            <thead>
              <tr>
                <th scope="col" rowspan="2" class="dialect">Dialect</th>
                <th scope="col" colspan="3">Tests</th>
                <th scope="col" rowspan="2">Badge</th>
              </tr>
              <tr>
                <th scope="col">Failed</th>
                <th scope="col">Skipped</th>
                <th scope="col">Errored</th>
              </tr>
            </thead>
            <tbody>
              {#each compliance as [dialect, totals] (dialect.uri)}
                <tr>
                  <th scope="row" class="dialect">{dialect.prettyName}</th>
                  <td class="num" class:bad={totals.failedTests}>{totals.failedTests ?? 0}</td>
                  <td class="num" class:bad={totals.skippedTests}>{totals.skippedTests ?? 0}</td>
                  <td class="num" class:bad={totals.erroredTests}>{totals.erroredTests ?? 0}</td>
                  <td>
                    <a href="#{dialect.routePath}">
                      <img class="badge" alt="{dialect.prettyName} compliance" src={impl.complianceBadgeFor(dialect).href()} />
                    </a>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>

      {#if impl.versions}
        <VersionsTrend implementation={impl} />
      {/if}
    </div>
  </div>
{/if}

<style>
  table.kv,
  table.compliance {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }
  table.kv th {
    text-align: left;
    font-weight: 560;
    color: var(--text-muted);
    padding: 6px 14px 6px 0;
    white-space: nowrap;
    vertical-align: top;
    width: 160px;
  }
  table.kv td {
    padding: 6px 0;
    word-break: break-word;
  }
  .muted {
    color: var(--text-muted);
  }
  table.compliance th,
  table.compliance td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
    text-align: center;
  }
  table.compliance thead th {
    color: var(--text-muted);
    font-weight: 560;
    font-size: 12px;
  }
  table.compliance .dialect {
    text-align: left;
    white-space: nowrap;
  }
  table.compliance .num {
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    color: var(--text-muted);
  }
  table.compliance .num.bad {
    color: var(--text);
    font-weight: 600;
  }
  .badge {
    max-width: 100%;
    vertical-align: middle;
  }
  .impl-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
  }
  .btn-badges {
    flex: none;
    margin-top: 6px;
    border: 1px solid var(--border-strong);
    background: var(--surface);
    color: var(--text);
    font-size: 12.5px;
    padding: 6px 14px;
    border-radius: 8px;
    cursor: pointer;
  }
  .btn-badges:hover,
  .btn-badges[aria-expanded="true"] {
    border-color: var(--accent);
    color: var(--accent);
  }
</style>
