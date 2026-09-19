import {
  AppWindow,
  Blocks,
  Bot,
  Boxes,
  Braces,
  BrainCircuit,
  ChartNoAxesCombined,
  CircuitBoard,
  Cloud,
  CloudCog,
  Code2,
  CodeXml,
  Cpu,
  Database,
  Gauge,
  GitBranch,
  Globe2,
  Laptop,
  Layers3,
  Lightbulb,
  LockKeyhole,
  MonitorSmartphone,
  Network,
  Rocket,
  SearchCode,
  Server,
  ServerCog,
  ShieldCheck,
  Smartphone,
  Sparkles,
  Terminal,
  Workflow,
  type LucideIcon,
} from "lucide-react";

import type { ServiceIconName } from "../../types/service";

export interface ServiceIconOption {
  name: ServiceIconName;
  label: string;
  icon: LucideIcon;
}

export const SERVICE_ICON_OPTIONS: ServiceIconOption[] = [
  { name: "Lightbulb", label: "Ideas", icon: Lightbulb },
  { name: "Code2", label: "Development", icon: Code2 },
  { name: "CodeXml", label: "Web code", icon: CodeXml },
  { name: "Terminal", label: "Terminal", icon: Terminal },
  { name: "Braces", label: "Programming", icon: Braces },
  { name: "Blocks", label: "Components", icon: Blocks },
  { name: "Workflow", label: "Automation", icon: Workflow },
  { name: "GitBranch", label: "Git", icon: GitBranch },
  { name: "Database", label: "Database", icon: Database },
  { name: "Server", label: "Backend", icon: Server },
  { name: "ServerCog", label: "Infrastructure", icon: ServerCog },
  { name: "Cloud", label: "Cloud", icon: Cloud },
  { name: "CloudCog", label: "Cloud systems", icon: CloudCog },
  { name: "Globe2", label: "Web", icon: Globe2 },
  {
    name: "MonitorSmartphone",
    label: "Responsive",
    icon: MonitorSmartphone,
  },
  { name: "Smartphone", label: "Mobile", icon: Smartphone },
  { name: "Laptop", label: "Applications", icon: Laptop },
  { name: "AppWindow", label: "Frontend", icon: AppWindow },
  { name: "BrainCircuit", label: "AI", icon: BrainCircuit },
  { name: "Bot", label: "AI agents", icon: Bot },
  { name: "Sparkles", label: "AI features", icon: Sparkles },
  { name: "Cpu", label: "Computing", icon: Cpu },
  { name: "CircuitBoard", label: "Systems", icon: CircuitBoard },
  { name: "Network", label: "Architecture", icon: Network },
  { name: "Boxes", label: "Platforms", icon: Boxes },
  { name: "Layers3", label: "Full stack", icon: Layers3 },
  { name: "Gauge", label: "Performance", icon: Gauge },
  { name: "Rocket", label: "Launch", icon: Rocket },
  { name: "ShieldCheck", label: "Security", icon: ShieldCheck },
  { name: "LockKeyhole", label: "Authentication", icon: LockKeyhole },
  {
    name: "ChartNoAxesCombined",
    label: "Analytics",
    icon: ChartNoAxesCombined,
  },
  { name: "SearchCode", label: "Code quality", icon: SearchCode },
];

const SERVICE_ICON_MAP = new Map(
  SERVICE_ICON_OPTIONS.map((option) => [option.name, option.icon]),
);

export function getServiceIcon(name: ServiceIconName): LucideIcon {
  return SERVICE_ICON_MAP.get(name) ?? Lightbulb;
}
