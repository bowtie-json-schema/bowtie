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
 * (filters + selection). Kept as a single reactive store so the rail, case
 * list, and detail stay in sync. Selection/filters are in-memory for now;
 * URL-syncing (`?case=`, `?language=`) is a follow-up.
 */
class ReportStore {
  data = $state<ReportData | null>(null);
  allImpls = $state<Map<string, Implementation>>(new Map());
  worst = $state<Map<number, Map<string, Worst>>>(new Map());

  // filters
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
    const langs = new Set<string>();
    for (const impl of data.runMetadata.implementations.values()) {
      langs.add(impl.language);
    }
    this.langs = langs;
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
    return [...this.d.runMetadata.implementations]
      .filter(([, i]) => this.langs.has(i.language))
      .map(([id]) => id);
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

  /**
   * Serialize the shareable slice of state (language filter + selected
   * case/test) to a query string. Ephemeral UI (status toggles, search text)
   * is intentionally left out of the URL.
   */
  toQuery(): string {
    const p = new URLSearchParams();
    const all = this.languages;
    if (this.langs.size && this.langs.size < all.length) {
      for (const l of all) if (this.langs.has(l)) p.append("language", l);
    }
    if (this.selectedSeq !== null) {
      p.set("case", String(this.selectedSeq));
      if (this.selectedTest) p.set("test", String(this.selectedTest));
    }
    return p.toString();
  }

  /** Restore filters/selection from a URL query (deep links, reloads). */
  applyQuery(params: URLSearchParams) {
    const langs = params
      .getAll("language")
      .filter((l) => this.languages.includes(l));
    if (langs.length) this.langs = new Set(langs);

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
