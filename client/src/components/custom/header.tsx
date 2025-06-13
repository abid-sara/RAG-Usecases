import { useTheme } from "@/context/ThemeContext";
import { Button } from "../ui/button";
import { SunIcon, MoonIcon } from "./icons";

export function Header() {
  const { theme, toggleTheme } = useTheme();

  // Function to format the current UTC date and time
  const formatDateTime = () => {
    const now = new Date();
    return now.toISOString().slice(0, 19).replace("T", " ");
  };

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between w-full px-4 py-2 bg-card/80 backdrop-blur-xl border-b">
      <div className="flex items-center space-x-4">
        <div className="flex flex-col text-sm">
          <span className="text-muted-foreground">{formatDateTime()} UTC</span>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="size-9"
        >
          {theme === "dark" ? <SunIcon /> : <MoonIcon />}
        </Button>
      </div>
    </header>
  );
}
