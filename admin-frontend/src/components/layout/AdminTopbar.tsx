import { Menu, Moon, Sun } from "lucide-react";
import { useLocation } from "react-router-dom";
import { useTheme } from "../../context/themeContext";
import { adminNavigation } from "./adminNavigation";

interface AdminTopbarProps {
  onMenuOpen: () => void;
}

function getPageTitle(pathname: string): string {
  const item = adminNavigation.find(({ path }) =>
    path === "/" ? pathname === "/" : pathname.startsWith(path),
  );

  return item?.label ?? "Administration";
}

export function AdminTopbar({ onMenuOpen }: AdminTopbarProps) {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="admin-topbar">
      <div className="admin-topbar__heading">
        <button
          className="admin-topbar__menu"
          type="button"
          onClick={onMenuOpen}
          aria-label="Open navigation"
        >
          <Menu size={23} />
        </button>

        <div>
          <span>Portfolio Administration</span>
          <strong>{getPageTitle(location.pathname)}</strong>
        </div>
      </div>

      <div className="admin-topbar__actions">
        <button
          className="admin-theme-toggle"
          type="button"
          onClick={toggleTheme}
          aria-label={
            theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
          }
          title={theme === "dark" ? "Light mode" : "Dark mode"}
        >
          {theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}

          <span>{theme === "dark" ? "Light" : "Dark"}</span>
        </button>

        <div
          className="admin-topbar__status"
          title="Administrator session active"
        >
          <span />
          Secure
        </div>
      </div>
    </header>
  );
}
