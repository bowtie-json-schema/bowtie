const KEY = "bowtie-theme";
const media = window.matchMedia("(prefers-color-scheme: dark)");
const stored = localStorage.getItem(KEY);

const initialDark = stored ? stored === "dark" : media.matches;
let dark = $state(initialDark);

function apply(d: boolean) {
  document.documentElement.setAttribute("data-theme", d ? "dark" : "light");
}
apply(initialDark);

// Follow the OS preference until the user makes an explicit choice.
if (!stored) {
  media.addEventListener("change", (e) => {
    if (!localStorage.getItem(KEY)) {
      dark = e.matches;
      apply(dark);
    }
  });
}

export const theme = {
  get dark() {
    return dark;
  },
  toggle() {
    dark = !dark;
    localStorage.setItem(KEY, dark ? "dark" : "light");
    apply(dark);
  },
};
