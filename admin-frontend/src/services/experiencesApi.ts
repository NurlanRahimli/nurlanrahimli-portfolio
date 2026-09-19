import { api } from "../lib/api";

import type {
  Experience,
  ExperienceList,
  ExperienceWritePayload,
} from "../types/experience";

export interface ListExperiencesParams {
  search?: string;
  isActive?: boolean;
  limit?: number;
  offset?: number;
}

export async function listExperiences({
  search,
  isActive,
  limit = 100,
  offset = 0,
}: ListExperiencesParams = {}): Promise<ExperienceList> {
  const response = await api.get<ExperienceList>("/experiences", {
    params: {
      search: search?.trim() || undefined,
      is_active: isActive,
      limit,
      offset,
    },
  });

  return response.data;
}

export async function createExperience(
  payload: ExperienceWritePayload,
): Promise<Experience> {
  const response = await api.post<Experience>("/experiences", payload);
  return response.data;
}

export async function updateExperience(
  experienceId: number,
  payload: ExperienceWritePayload,
): Promise<Experience> {
  const response = await api.put<Experience>(
    `/experiences/${experienceId}`,
    payload,
  );
  return response.data;
}

export async function deleteExperience(experienceId: number): Promise<void> {
  await api.delete(`/experiences/${experienceId}`);
}

export async function reorderExperiences(
  items: Array<{ id: number; display_order: number }>,
): Promise<void> {
  await api.post("/experiences/reorder", { items });
}
