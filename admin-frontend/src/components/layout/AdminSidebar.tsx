import { AnimatePresence, motion } from "framer-motion";
import { ExternalLink, LogOut, X } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/authContext";
import { adminNavigation } from "./adminNavigation";

interface AdminSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AdminSidebar({ isOpen, onClose }: AdminSidebarProps) {
  const { user, logout } = useAuth();

  const sidebarContent = (
    <>
      <div className="admin-sidebar__brand">
        <div className="admin-brand-mark">NR</div>

        <div className="admin-sidebar__brand-copy">
          <strong>Nurlan Rahimli</strong>
          <span>Portfolio Admin</span>
        </div>

        <button
          className="admin-sidebar__close"
          type="button"
          onClick={onClose}
          aria-label="Close navigation"
        >
          <X size={22} />
        </button>
      </div>

      <div className="admin-sidebar__section">
        <span className="admin-sidebar__label">Workspace</span>

        <nav className="admin-navigation" aria-label="Administration">
          {adminNavigation.map((item) => {
            const Icon = item.icon;

            if (!item.available) {
              return (
                <div
                  className="admin-navigation__item admin-navigation__item--disabled"
                  key={item.path}
                  title="Coming soon"
                >
                  <Icon size={20} />
                  <span>{item.label}</span>
                  <small>Soon</small>
                </div>
              );
            }

            return (
              <NavLink
                className={({ isActive }) =>
                  `admin-navigation__item${
                    isActive ? " admin-navigation__item--active" : ""
                  }`
                }
                end={item.path === "/"}
                key={item.path}
                to={item.path}
                onClick={onClose}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      <div className="admin-sidebar__footer">
        <a
          className="admin-sidebar__portfolio"
          href="https://nurlanrahimli.com"
          target="_blank"
          rel="noreferrer"
        >
          <ExternalLink size={18} />
          <span>View Portfolio</span>
        </a>

        <div className="admin-sidebar__account">
          <div className="admin-sidebar__avatar">NR</div>

          <div className="admin-sidebar__account-copy">
            <strong>Administrator</strong>
            <span>{user?.email}</span>
          </div>

          <button
            className="admin-sidebar__logout"
            type="button"
            onClick={logout}
            aria-label="Log out"
            title="Log out"
          >
            <LogOut size={19} />
          </button>
        </div>
      </div>
    </>
  );

  return (
    <>
      <aside className="admin-sidebar admin-sidebar--desktop">
        {sidebarContent}
      </aside>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.button
              className="admin-sidebar-overlay"
              type="button"
              aria-label="Close navigation"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
            />

            <motion.aside
              className="admin-sidebar admin-sidebar--mobile"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{
                duration: 0.28,
                ease: [0.22, 1, 0.36, 1],
              }}
            >
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
