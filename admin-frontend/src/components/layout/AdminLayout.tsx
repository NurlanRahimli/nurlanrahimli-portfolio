import { useState } from "react";
import { Outlet } from "react-router-dom";
import { AdminSidebar } from "./AdminSidebar";
import { AdminTopbar } from "./AdminTopbar";

export function AdminLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="admin-layout">
      <AdminSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      <div className="admin-layout__main">
        <AdminTopbar onMenuOpen={() => setIsSidebarOpen(true)} />

        <main className="admin-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
