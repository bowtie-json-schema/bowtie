const parseVersion = (version: string): (string | number)[] =>
  version.split(".").map((part) => (isNaN(Number(part)) ? part : Number(part)));

const sortVersions = (a: string, b: string): number => {
  const versionAParts = parseVersion(a);
  const versionBParts = parseVersion(b);

  for (
    let i = 0;
    i < Math.max(versionAParts.length, versionBParts.length);
    i++
  ) {
    if (versionAParts[i] === undefined) return -1;
    if (versionBParts[i] === undefined) return 1;
    if (versionAParts[i] < versionBParts[i]) return -1;
    if (versionAParts[i] > versionBParts[i]) return 1;
  }

  return 0;
};

export default sortVersions;
