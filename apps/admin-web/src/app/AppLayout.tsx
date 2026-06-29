import { Outlet, useLocation, useNavigate } from "react-router-dom";

import {
  DashboardIcon,
  ListIcon,
  LogoutIcon,
  PlaneIcon,
  UsersIcon,
} from "@/components/ui/icons";
import { useAuth } from "@/modules/auth/AuthContext";

import styles from "./AppLayout.module.css";

const NAV_ITEMS = [
  { key: "/dashboard", icon: DashboardIcon, label: "Dashboard" },
  { key: "/passengers", icon: UsersIcon, label: "Passageiros" },
  { key: "/validations", icon: ListIcon, label: "Validações" },
];

function getInitials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const activeKey =
    NAV_ITEMS.find((item) => location.pathname.startsWith(item.key))?.key ?? "/dashboard";

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <div className={styles.brandIcon}>
            <PlaneIcon />
          </div>
          <div>
            <span className={styles.brandName}>BFV Admin</span>
            <span className={styles.brandSub}>Boarding Face Validation</span>
          </div>
        </div>

        <div className={styles.navSection}>
          <span className={styles.navLabel}>Menu</span>
          <nav className={styles.nav}>
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = item.key === activeKey;
              return (
                <button
                  key={item.key}
                  type="button"
                  className={[styles.navItem, isActive ? styles.navItemActive : ""].join(" ")}
                  onClick={() => navigate(item.key)}
                >
                  {isActive && <span className={styles.navActiveBar} />}
                  <Icon className={styles.navIcon} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        <div className={styles.sidebarFooter}>
          <div className={styles.userRow}>
            <div className={styles.userAvatar}>
              {user?.full_name ? getInitials(user.full_name) : "?"}
            </div>
            <div className={styles.userInfo}>
              <span className={styles.userName}>{user?.full_name}</span>
              <span className={styles.userRole}>Administrador</span>
            </div>
            <button
              type="button"
              className={styles.logoutButton}
              onClick={logout}
              title="Sair"
              aria-label="Sair"
            >
              <LogoutIcon />
            </button>
          </div>
        </div>
      </aside>

      <main className={styles.content}>
        <Outlet />
      </main>
    </div>
  );
}
