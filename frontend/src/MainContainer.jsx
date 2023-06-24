import NavBar from "./components/NavBar";
import { useNavigation } from "react-router-dom";
import LoadingAnimation from "./components/LoadingAnimation";

export const MainContainer = ({ children }) => {
  const { state } = useNavigation();

  return (
    <div>
      <NavBar />
      {state === "loading" ? <LoadingAnimation /> : children}
    </div>
  );
};
