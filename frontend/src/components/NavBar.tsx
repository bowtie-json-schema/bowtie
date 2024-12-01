import { useContext, useEffect, useState } from "react";
import { Sun, MoonStarsFill, Book } from "react-bootstrap-icons";
import { Link, useLocation, useMatch } from "react-router";
import Container from "react-bootstrap/Container";
import Navbar from "react-bootstrap/Navbar";
import NavDropdown from "react-bootstrap/NavDropdown";
import Collapse from "react-bootstrap/Collapse";

import { ThemeContext } from "../context/ThemeContext";
import { BowtieVersionContext } from "../context/BowtieVersionContext";
import logo from "../assets/landscape-logo.svg";
import Dialect from "../data/Dialect";

const NavBar = () => {
  const { isDarkMode, toggleDarkMode } = useContext(ThemeContext);
  const { version } = useContext(BowtieVersionContext);
  const { hash, key } = useLocation();
  const [isNavbarOpen, setIsNavbarOpen] = useState(false);

  const rootMatch = useMatch("/");
  const dialectsMatch = useMatch("/dialects/*");
  const isBenchmarksPage = useMatch("/benchmarks/*");
  const isDialectPage = rootMatch ?? dialectsMatch;

  useEffect(() => {
    if (hash) {
      const targetElement = document.getElementById(hash.substring(1));
      targetElement?.scrollIntoView({ behavior: "smooth" });
    }
  }, [key, hash]);

  return (
    <Navbar
      expand="lg"
      sticky="top"
      className={`mb-4 ${
        isDarkMode ? "navbar-dark bg-dark" : "navbar-light bg-light"
      }`}
    >
      <Container
        fluid
        className="d-flex justify-content-between align-items-center"
      >
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
              type="button"
              className={`btn d-flex align-items-center justify-content-center ${
                isDarkMode ? "btn-light" : "btn-secondary"
              } rounded me-1 p-2`}
              onClick={() => toggleDarkMode!()}
            >
              {isDarkMode ? <MoonStarsFill size={20} /> : <Sun size={20} />}
            </button>
          </div>
          <Navbar.Toggle
            aria-controls="collapse-navbar-nav"
            aria-expanded="false"
            aria-label="Toggle navigation"
            onClick={() => setIsNavbarOpen(!isNavbarOpen)}
          />
        </div>
        <Collapse in={isNavbarOpen}>
          <div className="navbar-collapse" id="navbarSupportedContent">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0 align-items-baseline">
              {isDialectPage && (
                <>
                  <NavDropdown title="Dialects" id="dialect-dropdown">
                    {Dialect.newestToOldest().map((dialect) => (
                      <NavDropdown.Item
                        as={Link}
                        to={dialect.routePath}
                        key={dialect.shortName}
                      >
                        {dialect.prettyName}
                      </NavDropdown.Item>
                    ))}
                    <NavDropdown.Divider />
                    <NavDropdown.Item as={Link} to="/local-report/">
                      Upload a report
                    </NavDropdown.Item>
                  </NavDropdown>
                  <li className="nav-item">
                    <Link className="nav-link" to="/benchmarks">
                      Benchmarks
                    </Link>
                  </li>
                </>
              )}
              {isBenchmarksPage && (
                <>
                  <li className="nav-item">
                    <Link className="nav-link" to="/">
                      Dialect Test Reports
                    </Link>
                  </li>
                  <NavDropdown title="Dialects" id="dialect-dropdown">
                    {Dialect.newestToOldest().map((dialect) => (
                      <NavDropdown.Item
                        as={Link}
                        to={dialect.benchmarksRoutePath}
                        key={dialect.shortName}
                      >
                        {dialect.prettyName}
                      </NavDropdown.Item>
                    ))}
                  </NavDropdown>
                </>
              )}
              <li className="nav-item d-block d-lg-none">
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
              </li>
            </ul>
          </div>
        </Collapse>
        <div className="large-screen d-none d-lg-block">
          <Link
            className="nav-link border border-primary rounded-3 me-1 d-inline-block text-center py-2 px-3"
            to="https://docs.bowtie.report/"
            rel="noopener noreferrer"
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
      </Container>
    </Navbar>
  );
};

export default NavBar;
