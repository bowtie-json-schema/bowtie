import { useContext, useEffect } from "react";
import { Sun, MoonStarsFill, Book } from "react-bootstrap-icons";
import { Link, NavLink, useLocation, useMatch } from "react-router-dom";

import { ThemeContext } from "../context/ThemeContext";
import { BowtieVersionContext } from "../context/BowtieVersionContext";
import logo from "../assets/landscape-logo.svg";
import Dialect from "../data/Dialect";
import { Button } from "react-bootstrap";

const NavBar = () => {
  const { isDarkMode, toggleDarkMode } = useContext(ThemeContext);
  const { version } = useContext(BowtieVersionContext);
  const { hash, key } = useLocation();

  const rootMatch = useMatch("/");
  const dialectsMatch = useMatch("/dialects/*");
  const isDialectPage = rootMatch ?? dialectsMatch;

  useEffect(() => {
    if (hash) {
      const targetElement = document.getElementById(hash.substring(1));
      targetElement?.scrollIntoView({ behavior: "smooth" });
    }
  }, [key, hash]);

  return (
    <>
      <nav
        className={`navbar navbar-expand-lg sticky-top mb-4 ${
          isDarkMode ? "navbar-dark bg-dark" : "navbar-light bg-light"
        }`}
      >
        <div className="container-fluid d-flex justify-content-between align-items-center">
          <Link className="navbar-brand me-4 py-1" to="/">
            <img src={logo} alt="Bowtie Logo" width="128px" />
          </Link>
          <div className="d-flex align-items-center">
            <div className="d-lg-none d-flex justify-content-between align-items-center me-2">
              <Link
                className="nav-link border border-primary rounded-3 d-inline-block p-2 me-1"
                to="https://docs.bowtie.report/"
                target="_blank"
              >
                <Book size={20} />
              </Link>
              <button
                className={`btn d-flex align-items-center justify-content-center ${
                  isDarkMode ? "btn-light" : "btn-secondary"
                } rounded me-1 p-2`}
                onClick={() => toggleDarkMode!()}
              >
                {isDarkMode ? <MoonStarsFill size={20} /> : <Sun size={20} />}
              </button>
            </div>
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
          </div>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0 align-items-baseline">
              {isDialectPage && (
                <>
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
                </>
              )}
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
                  {Dialect.newest_to_oldest().map((dialect) => (
                    <li key={dialect.shortName}>
                      <NavLink
                        className="dropdown-item"
                        // FIXME: surely this shouldn't be hardcoded
                        to={`/dialects/${dialect.shortName}`}
                      >
                        {dialect.prettyName}
                      </NavLink>
                    </li>
                  ))}
                  <li>
                    <NavLink className="dropdown-item" to="/local-report/">
                      Local report
                    </NavLink>
                  </li>
                </ul>
              </li>
              <li className="nav-item d-block d-lg-none">
                <a
                  href="https://github.com/bowtie-json-schema/bowtie/"
                  className="link-secondary"
                  rel="noopener noreferrer"
                  target="_blank"
                >
                  <span className="navbar-text">
                    {version && `Bowtie v ${version}`}
                  </span>
                </a>
              </li>
            </ul>
          </div>
          <div className="large-screen d-none d-lg-block">
            <Link
              className="nav-link border border-primary rounded-3 me-1 d-inline-block text-center py-2 px-3"
              to="https://docs.bowtie.report/"
              target="_blank"
            >
              <Book size={20} className="me-1" />
              Docs
            </Link>
            <button
              className="btn border-0 me-1"
              onClick={() => toggleDarkMode!()}
            >
              {isDarkMode ? <MoonStarsFill size={20} /> : <Sun size={20} />}
            </button>
            <a
              href="https://github.com/bowtie-json-schema/bowtie/"
              className="link-secondary"
              rel="noopener noreferrer"
              target="_blank"
            >
              <span className="navbar-text">
                {version && <small>Bowtie v{version}</small>}
              </span>
            </a>
          </div>
        </div>
      </nav>
    </>
  );
};

export default NavBar;
