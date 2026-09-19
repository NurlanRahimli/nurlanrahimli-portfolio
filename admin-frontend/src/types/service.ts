export const SERVICE_ICON_NAMES = [
  "Lightbulb",
  "Code2",
  "CodeXml",
  "Terminal",
  "Braces",
  "Blocks",
  "Workflow",
  "GitBranch",
  "Database",
  "Server",
  "ServerCog",
  "Cloud",
  "CloudCog",
  "Globe2",
  "MonitorSmartphone",
  "Smartphone",
  "Laptop",
  "AppWindow",
  "BrainCircuit",
  "Bot",
  "Sparkles",
  "Cpu",
  "CircuitBoard",
  "Network",
  "Boxes",
  "Layers3",
  "Gauge",
  "Rocket",
  "ShieldCheck",
  "LockKeyhole",
  "ChartNoAxesCombined",
  "SearchCode",
] as const;

export type ServiceIconName = (typeof SERVICE_ICON_NAMES)[number];

export interface Service {
  id: number;
  icon: ServiceIconName;
  title: string;
  description: string;
  is_active: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface ServiceListResponse {
  items: Service[];
  total: number;
  limit: number;
  offset: number;
}

export interface ServicePayload {
  icon: ServiceIconName;
  title: string;
  description: string;
  is_active: boolean;
}

export interface ServiceReorderItem {
  id: number;
  display_order: number;
}
