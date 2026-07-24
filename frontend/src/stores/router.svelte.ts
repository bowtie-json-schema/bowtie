export interface Route {
  name: "dialect" | "benchmarks" | "implementation" | "local" | "notfound";
  params: Record<string, string | undefined>;
}

function parse(): { path: string; query: URLSearchParams } {
  const raw = location.hash.replace(/^#/, "") || "/";
  const [path, queryStr] = raw.split("?");
  return { path: path || "/", query: new URLSearchParams(queryStr ?? "") };
}

class Router {
  current = $state(parse());

  constructor() {
    window.addEventListener("hashchange", () => {
      this.current = parse();
    });
  }

  get path(): string {
    return this.current.path;
  }

  get query(): URLSearchParams {
    return this.current.query;
  }

  navigate(path: string) {
    location.hash = path;
  }
}

export const router = new Router();

export function matchRoute(path: string): Route {
  let m: RegExpMatchArray | null;
  if (path === "/") return { name: "dialect", params: {} };
  if ((m = path.match(/^\/dialects\/(.+?)\/?$/)))
    return { name: "dialect", params: { draftName: m[1] } };
  if ((m = path.match(/^\/benchmarks\/?(.*?)\/?$/)))
    return { name: "benchmarks", params: { draftName: m[1] || undefined } };
  if (path === "/local-report" || path === "/local-report/")
    return { name: "local", params: {} };
  if ((m = path.match(/^\/implementations\/([^/]+?)(?:\/(badges))?\/?$/)))
    return {
      name: "implementation",
      params: { id: m[1], badges: m[2] ? "1" : undefined },
    };
  return { name: "notfound", params: {} };
}
