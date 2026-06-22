import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { DashboardIcon, ListIcon, LogoutIcon, MoonIcon, SunIcon, UsersIcon } from "@/components/ui/icons";
import { useAuth } from "@/modules/auth/AuthContext";

import { useTheme } from "./theme/ThemeContext";
import styles from "./AppLayout.module.css";

const NAV_ITEMS = [
  { key: "/dashboard", icon: DashboardIcon, label: "Dashboard" },
  { key: "/passengers", icon: UsersIcon, label: "Passageiros" },
  { key: "/validations", icon: ListIcon, label: "Validações" },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const activeKey =
    NAV_ITEMS.find((item) => location.pathname.startsWith(item.key))?.key ?? "/dashboard";

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>Boarding Face Validation</div>
        <nav className={styles.nav}>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                type="button"
                className={[styles.navItem, item.key === activeKey ? styles.navItemActive : ""].join(
                  " ",
                )}
                onClick={() => navigate(item.key)}
              >
                <Icon className={styles.navIcon} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>

      <div className={styles.main}>
        <header className={styles.header}>
          <button
            type="button"
            className={styles.themeToggle}
            onClick={toggleTheme}
            aria-label="Alternar tema"
          >
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
          </button>
          <span className={styles.userName}>{user?.full_name}</span>
          <Button variant="ghost" size="sm" icon={<LogoutIcon />} onClick={logout}>
            Sair
          </Button>
        </header>

        <main className={styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
