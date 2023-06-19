import { useEffect, useState } from "react";
import { Sun, MoonStarsFill } from "react-bootstrap-icons";
import { Link, NavLink, useLocation } from "react-router-dom";

const NavBar = ({ runInfo }) => {
  const [mode, setMode] = useState(
    window.matchMedia("(prefers-color-scheme: dark)").matches,
  );
  const { hash, key } = useLocation();

  useEffect(() => {
    if (hash) {
      const targetElement = document.getElementById(hash.substring(1));
      targetElement?.scrollIntoView({ behavior: "smooth" });
    }
  }, [key, hash]);
  useEffect(() => {
    document
      .querySelector("body")
      .setAttribute("data-bs-theme", mode ? "dark" : "light");
  }, [mode]);

  return (
    <>
      <nav
        className={`navbar navbar-expand-lg sticky-top mb-4 ${
          mode ? "navbar-dark bg-dark" : "navbar-light bg-light"
        }`}
      >
        <div className="container-fluid">
          <a className="navbar-brand mb-0 h1" href="/">
            Bowtie
          </a>
          <button
            className="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarNav"
            aria-controls="navbarSupportedContent"
            aria-expanded="false"
            aria-label="Toggle navigation"
          >
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0">
              <li className="nav-item">
                <Link className="nav-link" to={{ hash: "run-info" }}>
                  Run Info
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to={{ hash: "summary" }}>
                  Summary
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to={{ hash: "cases" }}>
                  Details
                </Link>
              </li>
              <li className="nav-item dropdown">
                <a
                  className="nav-link dropdown-toggle"
                  role="button"
                  data-bs-toggle="dropdown"
                  aria-expanded="false"
                >
                  Dialects{" "}
                </a>
                <ul className="dropdown-menu">
                  <li>
                    <NavLink className="dropdown-item" to="/draft2020-12">
                      2020-12
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/draft2019-09">
                      2019-09
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/draft7">
                      7
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/draft6">
                      6
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/draft4">
                      4
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/draft3">
                      3
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/">
                      Local report
                    </NavLink>
                  </li>
                </ul>
              </li>
            </ul>
          </div>
          <button
            id="theme-toggler"
            className="btn border-0 me-1"
            onClick={() => setMode(!mode)}
          >
            {mode ? <MoonStarsFill size={20} /> : <Sun size={20} />}
          </button>
          <a
            href="https://github.com/bowtie-json-schema/bowtie/"
            className="link-secondary"
          >
            <span className="navbar-text">
             {runInfo ? <small>Bowtie v - {runInfo.bowtieVersion}</small> : null }
            </span>
          </a>
        </div>
      </nav>
    </>
  );
};

export default NavBar;
