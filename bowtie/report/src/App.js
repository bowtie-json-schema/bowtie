import RawData from "./data/RawData";

function App(props) {
  // console.log(props.dataObjectsArray)
  return (
    <div>
      Hello World!
      <RawData data = {props.dataObjectsArray} />
      </div>
  );
}

export default App;
