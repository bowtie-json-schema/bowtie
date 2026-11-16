import URI from "urijs";

import { BADGES } from "./Badge";
import type Dialect from "./Dialect";

/**
 * How an implementation fares in Bowtie on one dialect, read from its compliance badge. Bowtie truncates the badge's
 * percentage, so 100 means that every test passed, with nothing failed, errored or skipped.
 */
export type Compliance =
  | { state: "tested"; percent: number }
  /** Bowtie tests the implementation, but not on this dialect */
  | { state: "unsupported" }
  /** the benchmark does not link the implementation to Bowtie */
  | { state: "untested" }
  /** the benchmark links it to an ID that Bowtie does not know: a typo, or an implementation renamed or retired */
  | { state: "unrecognized" }
  /** the badge could not be loaded or read */
  | { state: "unknown" };

const MESSAGE = /^(\d{1,3})% Passing$/;

export function parseComplianceBadge(badge: unknown): Compliance {
  const message = (badge as { message?: unknown } | null)?.message;
  const match = typeof message === "string" ? MESSAGE.exec(message) : null;
  return match ? { state: "tested", percent: Number(match[1]) } : { state: "unknown" };
}

export const isFullyCompliant = (compliance: Compliance | undefined) =>
  compliance?.state === "tested" && compliance.percent === 100;

export function complianceBadgeURI(bowtieId: string, dialect: Dialect, badges: URI = BADGES): URI {
  // segment(string) appends; segment(array) would replace the whole path.
  return badges.clone().segment(bowtieId).segment("compliance").segment(`${dialect.shortName}.json`);
}

/** Bowtie publishes this for every implementation it knows, whichever dialects it tests. */
export function supportedVersionsURI(bowtieId: string, badges: URI = BADGES): URI {
  return badges.clone().segment(bowtieId).segment("supported_versions.json");
}

/** Why an implementation has no badge for a dialect: Bowtie does not test it on that dialect, or does not know it. */
async function withoutBadge(bowtieId: string, badges: URI): Promise<Compliance> {
  const response = await fetch(supportedVersionsURI(bowtieId, badges).href());
  if (response.ok) return { state: "unsupported" };
  return response.status === 404 ? { state: "unrecognized" } : { state: "unknown" };
}

/** The compliance of each Bowtie implementation on the dialect, keyed by Bowtie ID. */
export async function fetchCompliance(
  bowtieIds: Iterable<string>,
  dialect: Dialect,
  badges: URI = BADGES,
): Promise<Map<string, Compliance>> {
  const ids = [...new Set(bowtieIds)];
  const entries = await Promise.all(
    ids.map(async (id): Promise<[string, Compliance]> => {
      try {
        const response = await fetch(complianceBadgeURI(id, dialect, badges).href());
        if (response.status === 404) return [id, await withoutBadge(id, badges)];
        if (!response.ok) return [id, { state: "unknown" }];
        return [id, parseComplianceBadge(await response.json())];
      } catch {
        return [id, { state: "unknown" }];
      }
    }),
  );
  return new Map(entries);
}
