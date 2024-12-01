import { useNavigation, useOutlet } from "react-router";

import LoadingAnimation from "./components/LoadingAnimation";
import NavBar from "./components/NavBar";

export const MainContainer = () => {
  const { state } = useNavigation();
  const outlet = useOutlet();

  return (
    <>
      <NavBar />
      {state === "loading" ? <LoadingAnimation /> : outlet}
    </>
  );
};
