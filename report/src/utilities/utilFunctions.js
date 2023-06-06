class _Summary {
  constructor(implementations) {
    // console.log(typeof(implementations.implementations))
    // console.log((implementations['implementations']))
    const implementationArray = Object.values(implementations);
    // console.log(implementationArray[0])

    this.implementations = implementationArray[0].sort((each, other) => {
      const key = `${each.language}${each.name}`;
      const otherKey = `${other.language}${other.name}`;
      return key < otherKey ? -1 : 1;
    });
    // console.log(this.implementations)
    this.didFailFastast = false;
  }
}
const tooltipTriggerList = document.querySelectorAll(
  '[data-bs-toggle="tooltip"]'
);
const tooltipList = [...tooltipTriggerList].map(
  (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl)
);

export function schemaDisplay(parentBodyId, code, targetId, rowClass) {
  let currentParentBodyId = "";
  const displayBody = document.getElementById("display-body");
  if (parentBodyId !== currentParentBodyId) {
    currentParentBodyId = parentBodyId;
    displayBody.classList.remove("d-none");
    displayBody.classList.add("d-block");
    document.getElementById("instance-info").innerHTML = "";

    const isDisplayed =
      displayBody.parentElement === document.getElementById(parentBodyId);

    if (isDisplayed) {
      displayBody.parentElement.removeChild(displayBody);
    } else {
      // Add Highlight Row Functionality to clicked accordion only
      rowHighlightListener(rowClass);
      displayCode(code, targetId);
      const accordionBody = document.querySelector(`#${parentBodyId}`);
      accordionBody.insertBefore(displayBody, accordionBody.firstChild);
    }
  }

  function rowHighlightListener(rowClass) {
    const instanceRows = document.getElementsByClassName(rowClass);
    for (let i = 0; i < instanceRows.length; i++) {
      const currentInstanceRow = instanceRows[i];
      currentInstanceRow.addEventListener("click", function () {
        const activeElements = document.getElementsByClassName("table-active");
        for (let j = 0; j < activeElements.length; j++) {
          activeElements[j].classList.remove("table-active");
        }
        currentInstanceRow.classList.add("table-active");
      });
    }
  }

  function displayCode(code, targetId) {
    const targetDisplay = document.getElementById(targetId);
    displayBody.classList.remove("d-none");
    displayBody.classList.add("d-block");
    targetDisplay.innerHTML = `<pre>${code}</pre>`;
  }
}
