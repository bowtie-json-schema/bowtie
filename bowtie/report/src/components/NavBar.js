import { useState } from "react";

const NavBar = ({ runInfo }) => {
  const generate_dialect_navigation = true;
  const body = document.querySelector("body");
  const [mode, setMode] = useState(
    window.matchMedia("(prefers-color-scheme: dark)").matches,
  );

  body.setAttribute("data-bs-theme", mode ? "dark" : "light");

  function toggleMode() {
    const newMode = !mode;
    setMode(newMode);
  }

  return (
    <>
      <nav
        className={`navbar navbar-expand-lg sticky-top mb-4 ${
          mode ? "navbar-dark bg-dark" : "navbar-light bg-light"
        }`}
      >
        <div className="container-fluid">
          <a className="navbar-brand mb-0 h1" href="#">
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
                <a className="nav-link" href="#run-info">
                  Run Info
                </a>
              </li>
              <li className="nav-item">
                <a className="nav-link" href="#summary">
                  Summary
                </a>
              </li>
              <li className="nav-item">
                <a className="nav-link" href="#cases">
                  Details
                </a>
              </li>
              {generate_dialect_navigation && (
                <li className="nav-item dropdown">
                  <a
                    className="nav-link dropdown-toggle"
                    href="#"
                    role="button"
                    data-bs-toggle="dropdown"
                    aria-expanded="false"
                  >
                    Dialects
                  </a>
                  <ul className="dropdown-menu">
                    <li>
                      <a className="dropdown-item" href="draft2020-12">
                        2020-12
                      </a>
                    </li>
                    <li>
                      <a className="dropdown-item" href="draft2019-09">
                        2019-09
                      </a>
                    </li>
                    <li>
                      <a className="dropdown-item" href="draft7">
                        7
                      </a>
                    </li>
                    <li>
                      <a className="dropdown-item" href="draft6">
                        6
                      </a>
                    </li>
                    <li>
                      <a className="dropdown-item" href="draft4">
                        4
                      </a>
                    </li>
                    <li>
                      <a className="dropdown-item" href="draft3">
                        3
                      </a>
                    </li>
                  </ul>
                </li>
              )}
            </ul>
          </div>
          <button
            id="theme-toggler"
            className="btn border-0 me-1"
            onClick={toggleMode}
          >
            {mode ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                fill="currentColor"
                className="bi bi-moon-stars-fill"
                viewBox="0 0 16 16"
              >
                <path d="M6 .278a.768.768 0 0 1 .08.858 7.208 7.208 0 0 0-.878 3.46c0 4.021 3.278 7.277 7.318 7.277.527 0 1.04-.055 1.533-.16a.787.787 0 0 1 .81.316.733.733 0 0 1-.031.893A8.349 8.349 0 0 1 8.344 16C3.734 16 0 12.286 0 7.71 0 4.266 2.114 1.312 5.124.06A.752.752 0 0 1 6 .278z" />
                <path d="M10.794 3.148a.217.217 0 0 1 .412 0l.387 1.162c.173.518.579.924 1.097 1.097l1.162.387a.217.217 0 0 1 0 .412l-1.162.387a1.734 1.734 0 0 0-1.097 1.097l-.387 1.162a.217.217 0 0 1-.412 0l-.387-1.162A1.734 1.734 0 0 0 9.31 6.593l-1.162-.387a.217.217 0 0 1 0-.412l1.162-.387a1.734 1.734 0 0 0 1.097-1.097l.387-1.162zM13.863.099a.145.145 0 0 1 .274 0l.258.774c.115.346.386.617.732.732l.774.258a.145.145 0 0 1 0 .274l-.774.258a1.156 1.156 0 0 0-.732.732l-.258.774a.145.145 0 0 1-.274 0l-.258-.774a1.156 1.156 0 0 0-.732-.732l-.774-.258a.145.145 0 0 1 0-.274l.774-.258c.346-.115.617-.386.732-.732L13.863.1z" />
              </svg>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                fill="currentColor"
                className="bi bi-sun"
                viewBox="0 0 16 16"
              >
                <path d="M8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm0 1a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM8 0a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 0zm0 13a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 13zm8-5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2a.5.5 0 0 1 .5.5zM3 8a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2A.5.5 0 0 1 3 8zm10.657-5.657a.5.5 0 0 1 0 .707l-1.414 1.415a.5.5 0 1 1-.707-.708l1.414-1.414a.5.5 0 0 1 .707 0zm-9.193 9.193a.5.5 0 0 1 0 .707L3.05 13.657a.5.5 0 0 1-.707-.707l1.414-1.414a.5.5 0 0 1 .707 0zm9.193 2.121a.5.5 0 0 1-.707 0l-1.414-1.414a.5.5 0 0 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .707zM4.464 4.465a.5.5 0 0 1-.707 0L2.343 3.05a.5.5 0 1 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .708z" />
              </svg>
            )}
          </button>
          <a
            href="https://github.com/bowtie-json-schema/bowtie/"
            className="link-secondary"
          >
            <span className="navbar-text">
              <small>Bowtie v - {runInfo.bowtie_version}</small>
            </span>
          </a>
        </div>
      </nav>
    </>
  );
};

export default NavBar;
