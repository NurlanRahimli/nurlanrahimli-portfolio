import {
  FolderKanban,
  Image,
  LayoutDashboard,
  Mail,
  PanelsTopLeft,
  type LucideIcon,
  MessageSquareQuote,
} from "lucide-react";

export interface AdminNavigationItem {
  label: string;
  path: string;
  icon: LucideIcon;
  available: boolean;
}

export const adminNavigation: AdminNavigationItem[] = [
  {
    label: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
    available: true,
  },
  {
    label: "Media Library",
    path: "/media",
    icon: Image,
    available: true,
  },
  {
    label: "Projects",
    path: "/projects",
    icon: FolderKanban,
    available: true,
  },
  {
    label: "Testimonials",
    path: "/testimonials",
    icon: MessageSquareQuote,
    available: true,
  },
  {
    label: "Website Content",
    path: "/content",
    icon: PanelsTopLeft,
    available: true,
  },
  {
    label: "Contact Inquiries",
    path: "/inquiries",
    icon: Mail,
    available: false,
  },
];
