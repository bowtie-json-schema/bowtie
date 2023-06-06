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

// export function schemaDisplay(parentBodyId, code, targetId, rowClass) {
//   let currentParentBodyId = null;
//   const displayBody = document.getElementById("display-body");

//   if (parentBodyId !== currentParentBodyId) {
//     currentParentBodyId = parentBodyId;
//     displayBody.classList.remove("d-none");
//     displayBody.classList.add("d-block");
//     document.getElementById("instance-info").innerHTML = "";

//     const isDisplayed =
//       displayBody.parentElement === document.getElementById(parentBodyId);

//     if (isDisplayed) {
//       displayBody.parentElement.removeChild(displayBody);
//     } else {
//       // Add Highlight Row Functionality to clicked accordion only
//       rowHighlightListener(rowClass);
//       displayCode(code, targetId);
//       const accordionBody = document.querySelector(`#${parentBodyId}`);
//       accordionBody.insertBefore(displayBody, accordionBody.firstChild);
//     }
//   }
// }

// function rowHighlightListener(rowClass) {
//   const instanceRows = document.getElementsByClassName(rowClass);
//   for (let i = 0; i < instanceRows.length; i++) {
//     const currentInstanceRow = instanceRows[i];
//     currentInstanceRow.addEventListener("click", function () {
//       const activeElements = document.getElementsByClassName("table-active");
//       for (let j = 0; j < activeElements.length; j++) {
//         activeElements[j].classList.remove("table-active");
//       }
//       currentInstanceRow.classList.add("table-active");
//     });
//   }
// }

// function displayCode(code, targetId) {
//   const targetDisplay = document.getElementById(targetId);
//   displayBody.classList.remove("d-none");
//   displayBody.classList.add("d-block");
//   targetDisplay.innerHTML = `<pre>${code}</pre>`;
// }

// export function to_icon(valid) {
//   if (valid === true) {
//     // Circular Checkmark SVG Icon
//     return `
//         <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check-circle-fill" viewBox="0 0 16 16">
//           <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z" />
//         </svg>
//       `;
//   } else if (valid === false) {
//     // Circular cross (x) SVG Icon
//     return `
//         <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x-circle-fill" viewBox="0 0 16 16">
//           <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z" />
//         </svg>
//       `;
//   } else {
//     // Circular warning (!) SVG Icon
//     return `
//         <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-exclamation-octagon" viewBox="0 0 16 16">
//           <path d="M4.54.146A.5.5 0 0 1 4.893 0h6.214a.5.5 0 0 1 .353.146l4.394 4.394a.5.5 0 0 1 .146.353v6.214a.5.5 0 0 1-.146.353l-4.394 4.394a.5.5 0 0 1-.353.146H4.893a.5.5 0 0 1-.353-.146L.146 11.46A.5.5 0 0 1 0 11.107V4.893a.5.5 0 0 1 .146-.353L4.54.146zM5.1 1 1 5.1v5.8L5.1 15h5.8l4.1-4.1V5.1L10.9 1H5.1z" />
//           <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z" />
//         </svg>
//       `;
//   }
// }
