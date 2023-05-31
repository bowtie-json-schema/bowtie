import { useState } from 'react';
import moonIcon from '../assets/svg/moonIcon.svg';
import sunIcon from '../assets/svg/sunIcon.svg';

const NavBar = ({ runInfo }) => {
  const generate_dialect_navigation = true;
  const body = document.querySelector("body");
  const [mode, setMode] = useState(window.matchMedia("(prefers-color-scheme: dark)").matches);

  body.setAttribute("data-bs-theme", mode ? "dark" : "light");
  function toggleMode() {
    const newMode = !mode;
    setMode(newMode);
  
  }


  return (
    <>
      <nav className={`navbar navbar-expand-lg sticky-top mb-4 ${mode ? 'navbar-dark bg-dark' : 'navbar-light-bg-light'}`}>
        <div className="container-fluid">
          <a className="navbar-brand mb-0 h1" href="#">Bowtie</a>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
            aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0">
              <li className="nav-item">
                <a className="nav-link" href="#run-info">Run Info</a>
              </li>
              <li className="nav-item">
                <a className="nav-link" href="#summary">Summary</a>
              </li>
              <li className="nav-item">
                <a className="nav-link" href="#cases">Details</a>
              </li>
              {generate_dialect_navigation && (
                <li className="nav-item dropdown">
                  <a className="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                    Dialects
                  </a>
                  <ul className="dropdown-menu">
                    <li><a className="dropdown-item" href="draft2020-12">2020-12</a></li>
                    <li><a className="dropdown-item" href="draft2019-09">2019-09</a></li>
                    <li><a className="dropdown-item" href="draft7">7</a></li>
                    <li><a className="dropdown-item" href="draft6">6</a></li>
                    <li><a className="dropdown-item" href="draft4">4</a></li>
                    <li><a className="dropdown-item" href="draft3">3</a></li>
                  </ul>
                </li>
              )}
            </ul>
          </div>
          <button id="theme-toggler" className="btn border-0 me-1" onClick={toggleMode}>
            {
                mode ? <img src={moonIcon} /> : <img src={sunIcon} />
            }
          </button>
          <a href="https://github.com/bowtie-json-schema/bowtie/" className="link-secondary">
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
