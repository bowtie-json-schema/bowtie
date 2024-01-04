import NavBar from "./components/NavBar";
import { useNavigation, useOutlet } from "react-router-dom";
import LoadingAnimation from "./components/LoadingAnimation";

export const MainContainer = () => {
  const { state } = useNavigation();
  const outlet = useOutlet();

  return (
    <div>
      <NavBar />
      {state === "loading" ? <LoadingAnimation /> : outlet}
    </div>
  );
};
