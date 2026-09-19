import { api } from "../lib/api";
import type {
  Skill,
  SkillListResponse,
  SkillPayload,
  SkillReorderItem,
} from "../types/skill";

interface GetSkillsParams {
  search?: string;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}

export async function getSkills(
  params: GetSkillsParams = {},
): Promise<SkillListResponse> {
  const response = await api.get<SkillListResponse>("/skills", { params });
  return response.data;
}

export async function createSkill(payload: SkillPayload): Promise<Skill> {
  const response = await api.post<Skill>("/skills", payload);
  return response.data;
}

export async function updateSkill(
  id: number,
  payload: SkillPayload,
): Promise<Skill> {
  const response = await api.put<Skill>(`/skills/${id}`, payload);
  return response.data;
}

export async function deleteSkill(id: number): Promise<void> {
  await api.delete(`/skills/${id}`);
}

export async function reorderSkills(items: SkillReorderItem[]): Promise<void> {
  await api.post("/skills/reorder", { items });
}
