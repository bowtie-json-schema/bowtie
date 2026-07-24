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
  import Breadcrumbs from "../components/Breadcrumbs.svelte";
  import Spinner from "../components/Spinner.svelte";

  let { id, badges = false }: { id: string; badges?: boolean } = $props();

  let impl = $state<Implementation | null>(null);
  let compliance = $state<[Dialect, Partial<Totals>][]>([]);
  let reports = $state<Map<Dialect, ReportData> | null>(null);
  let loading = $state(true);
  let notFound = $state(false);
  let error = $state<string | null>(null);
  let showBadges = $state(false);
  let loadToken = 0;

  $effect(() => {
    if (badges) showBadges = true;
  });

  const badTotal = (t: Partial<Totals>) =>
    (t.failedTests ?? 0) + (t.erroredTests ?? 0) + (t.skippedTests ?? 0);

  async function load(implId: string) {
    const token = ++loadToken;
    loading = true;
    notFound = false;
    error = null;
    document.title = `Bowtie – ${implId}`;
    try {
      const [, allReports] = await Promise.all([
        Implementation.fetchAllImplementationsData(),
        Dialect.fetchAllReports(),
      ]);
      if (token !== loadToken) return; // superseded by a newer navigation
      const found = Implementation.withId(implId);
      if (!found) {
        notFound = true;
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
    } catch (e) {
      if (token === loadToken) error = e instanceof Error ? e.message : String(e);
    } finally {
      if (token === loadToken) loading = false;
    }
  }

  $effect(() => {
    void load(id);
  });
</script>

{#if loading}
  <Spinner />
{:else if error}
  <div class="doc">
    <div class="doc-inner">
      <h1 class="page">Couldn’t load this implementation</h1>
      <div class="empty-note">{error}<br /><a href="#/">Back to the report</a></div>
    </div>
  </div>
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
      <Breadcrumbs />
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
              {#if impl.links?.some((l) => l.url)}
                <tr>
                  <th>Additional links</th>
                  <td>
                    <ul class="links">
                      {#each impl.links as link, i (i)}
                        {#if link.url}
                          <li><a href={link.url}>{link.description ?? link.url}</a></li>
                        {/if}
                      {/each}
                    </ul>
                  </td>
                </tr>
              {/if}
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
  table.compliance {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }
  .muted {
    color: var(--text-muted);
  }
  ul.links {
    margin: 0;
    padding-left: 18px;
    display: flex;
    flex-direction: column;
    gap: 3px;
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
