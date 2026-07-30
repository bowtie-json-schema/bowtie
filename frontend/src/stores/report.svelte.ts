import type Implementation from "../data/Implementation";
import type { ReportData } from "../data/parseReportData";
import {
  computeWorst,
  emptyCounts,
  type Counts,
  type Worst,
} from "../lib/reportModel";

/**
 * Holds the currently-loaded dialect report plus all cross-pane UI state
 * (filters + selection), kept as a single reactive store so the rail, case
 * list, and detail stay in sync. Filters + selection round-trip through the URL
 * via {@link toQuery}/{@link applyQuery}.
 */
class ReportStore {
  data = $state<ReportData | null>(null);
  allImpls = $state<Map<string, Implementation>>(new Map());
  worst = $state<Map<number, Map<string, Worst>>>(new Map());

  // filters. An empty `langs` set means "all languages" (no filter); the first
  // click on a language narrows to just it, further clicks add/remove.
  langs = $state<Set<string>>(new Set());
  statuses = $state<Set<Worst>>(new Set<Worst>(["fail", "err", "skip"]));
  search = $state("");
  showPassing = $state(false);

  // selection
  selectedSeq = $state<number | null>(null);
  selectedTest = $state(0);
  openDiag = $state<string | null>(null);

  load(data: ReportData, allImpls: Map<string, Implementation> = new Map()) {
    this.data = data;
    this.allImpls = allImpls;
    this.worst = computeWorst(data);
    this.langs = new Set(); // empty = all languages
    this.statuses = new Set<Worst>(["fail", "err", "skip"]);
    this.search = "";
    this.showPassing = false;
    this.selectedSeq = null;
    this.selectedTest = 0;
    this.openDiag = null;
  }

  private get d(): ReportData {
    return this.data!;
  }

  get languages(): string[] {
    const s = new Set<string>();
    if (this.data) {
      for (const i of this.d.runMetadata.implementations.values()) {
        s.add(i.language);
      }
    }
    return [...s].sort();
  }

  get scopedImplIds(): string[] {
    if (!this.data) return [];
    const all = this.langs.size === 0;
    return [...this.d.runMetadata.implementations]
      .filter(([, i]) => all || this.langs.has(i.language))
      .map(([id]) => id);
  }

  /**
   * Implementations Bowtie knows about that are in scope by language but absent
   * from this dialect's report (i.e. they don't support the current dialect),
   * sorted by name.
   */
  get otherImpls(): Implementation[] {
    if (!this.data) return [];
    return [...this.allImpls.values()]
      .filter(
        (i) =>
          (this.langs.size === 0 || this.langs.has(i.language)) &&
          !this.d.implementationsResults.has(i.id),
      )
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  countsWorst(seq: number): Counts {
    const n = emptyCounts();
    const m = this.worst.get(seq);
    if (!m) return n;
    for (const id of this.scopedImplIds) n[m.get(id) ?? "err"]++;
    return n;
  }

  nDisagree(seq: number): number {
    const n = this.countsWorst(seq);
    return n.fail + n.err + n.skip;
  }

  private isFailing(seq: number): boolean {
    return this.nDisagree(seq) > 0;
  }

  private matchesStatus(seq: number): boolean {
    const m = this.worst.get(seq);
    if (!m) return false;
    return this.scopedImplIds.some((id) => {
      const w = m.get(id) ?? "err";
      return w !== "ok" && this.statuses.has(w);
    });
  }

  private matchesSearch(seq: number): boolean {
    if (!this.search) return true;
    const c = this.d.cases.get(seq)!;
    const hay = (
      c.description +
      " " +
      c.tests.map((t) => t.description).join(" ")
    ).toLowerCase();
    return hay.includes(this.search.toLowerCase());
  }

  get failingSeqs(): number[] {
    if (!this.data) return [];
    return [...this.d.cases.keys()]
      .filter(
        (s) => this.isFailing(s) && this.matchesStatus(s) && this.matchesSearch(s),
      )
      .sort((a, b) => this.nDisagree(b) - this.nDisagree(a));
  }

  get passingSeqs(): number[] {
    if (!this.data) return [];
    return [...this.d.cases.keys()].filter(
      (s) => !this.isFailing(s) && this.matchesSearch(s),
    );
  }

  toggleLang(lang: string) {
    const next = new Set(this.langs);
    if (next.has(lang)) next.delete(lang);
    else next.add(lang);
    this.langs = next;
  }

  toggleStatus(s: Worst) {
    const next = new Set(this.statuses);
    if (next.has(s)) next.delete(s);
    else next.add(s);
    this.statuses = next;
  }

  select(seq: number) {
    this.selectedSeq = seq;
    this.selectedTest = 0;
    this.openDiag = null;
  }

  selectTest(idx: number) {
    this.selectedTest = idx;
    this.openDiag = null;
  }

  private static readonly DEFAULT_STATUS = ["err", "fail", "skip"];

  /**
   * Serialize the filter + selection state to a query string so a view is
   * shareable and survives reload. Defaults (all languages, the default status
   * set, no search) are omitted to keep URLs tidy.
   */
  toQuery(): string {
    const p = new URLSearchParams();
    if (this.langs.size) {
      for (const l of this.languages) if (this.langs.has(l)) p.append("language", l);
    }
    const cur = [...this.statuses].sort();
    if (cur.join(",") !== ReportStore.DEFAULT_STATUS.join(",")) {
      if (cur.length === 0) p.set("status", "none");
      else for (const s of cur) p.append("status", s);
    }
    if (this.showPassing) p.set("passing", "1");
    if (this.search) p.set("q", this.search);
    if (this.selectedSeq !== null) {
      p.set("case", String(this.selectedSeq));
      if (this.selectedTest) p.set("test", String(this.selectedTest));
    }
    return p.toString();
  }

  /** Restore filters/selection from a URL query (deep links, reloads). */
  applyQuery(params: URLSearchParams) {
    this.langs = new Set(
      params.getAll("language").filter((l) => this.languages.includes(l)),
    );

    const valid: Worst[] = ["fail", "err", "skip"];
    if (params.get("status") === "none") {
      this.statuses = new Set();
    } else {
      const statuses = params
        .getAll("status")
        .filter((s): s is Worst => valid.includes(s as Worst));
      if (statuses.length) this.statuses = new Set(statuses);
    }
    this.showPassing = params.get("passing") === "1";
    this.search = params.get("q") ?? "";

    const caseParam = params.get("case");
    if (caseParam !== null) {
      const seq = Number(caseParam);
      if (Number.isInteger(seq) && this.data?.cases.has(seq)) {
        this.selectedSeq = seq;
        const test = Number(params.get("test"));
        this.selectedTest = Number.isInteger(test) && test > 0 ? test : 0;
      }
    }
  }
}

export const report = new ReportStore();
