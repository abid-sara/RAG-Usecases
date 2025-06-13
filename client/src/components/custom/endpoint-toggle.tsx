import { useState } from "react";
import { Button } from "@/components/ui/button";

interface ToggleButtonProps {
  endpoints: [string, string];
  onToggle: (selectedEndpoint: string) => void;
}

const ToggleButton: React.FC<ToggleButtonProps> = ({ endpoints, onToggle }) => {
  const [selected, setSelected] = useState(0);

  const handleToggle = () => {
    const newSelected = 1 - selected;
    setSelected(newSelected);
    onToggle(endpoints[newSelected]);
  };

  return (
    <Button onClick={handleToggle} className="px-4 py-2 rounded-lg">
      Using: {endpoints[selected] == "http://localhost:5000/api/qa"? "IF-IDF" : "Hybrid Search"}
    </Button>
  );
};

export default ToggleButton;
