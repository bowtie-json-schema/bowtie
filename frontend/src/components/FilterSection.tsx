import { Link } from "react-router";
import Badge from "react-bootstrap/Badge";
import Card from "react-bootstrap/Card";
import { X } from "react-bootstrap-icons";

import { useSearchParams } from "../hooks/useSearchParams.ts";
import { mapLanguage } from "../data/mapLanguage.ts";
import styles from "./FilterSection.module.css";

export const FilterSection = ({ languages }: { languages: string[] }) => {
  const params = useSearchParams();

  return (
    <Card className="mx-auto mb-3">
      <Card.Header>Filtering</Card.Header>
      <Card.Body>
        <Card.Title>Language</Card.Title>
        <div className="d-flex flex-wrap gap-2 py-2">
          {languages.map((lang) => (
            <FilterChip key={lang} current={lang} searchParams={params} />
          ))}
        </div>
      </Card.Body>
    </Card>
  );
};

const FilterChip = ({
  current,
  searchParams,
}: {
  current: string;
  searchParams: URLSearchParams;
}) => {
  const languages = searchParams.getAll("language");
  if (languages.includes(current)) {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete("language");
    languages
      .filter((lang) => lang !== current)
      .forEach((lang) => newParams.append("language", lang));
    return (
      <Link key={current} to={{ search: newParams.toString() }}>
        <Badge pill bg="" className={styles["bg-filter-active"]}>
          <div className="px-2">{mapLanguage(current)}</div>
          <X size="20px" className="mr-1" />
        </Badge>
      </Link>
    );
  } else {
    const newParams = new URLSearchParams(searchParams);
    newParams.append("language", current);
    return (
      <Link key={current} to={{ search: newParams.toString() }}>
        <Badge pill bg="" className={styles["bg-filter"]}>
          <div className="px-2">{mapLanguage(current)}</div>
        </Badge>
      </Link>
    );
  }
};
