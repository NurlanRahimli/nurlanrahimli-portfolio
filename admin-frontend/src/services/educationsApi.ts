import { api } from "../lib/api";
import type {
  Education,
  EducationList,
  EducationWritePayload,
} from "../types/education";

export interface ListEducationsParams {
  search?: string;
  isActive?: boolean;
  limit?: number;
  offset?: number;
}

export async function listEducations({
  search,
  isActive,
  limit = 100,
  offset = 0,
}: ListEducationsParams = {}): Promise<EducationList> {
  const response = await api.get<EducationList>("/educations", {
    params: {
      search: search?.trim() || undefined,
      is_active: isActive,
      limit,
      offset,
    },
  });

  return response.data;
}

export async function createEducation(
  payload: EducationWritePayload,
): Promise<Education> {
  const response = await api.post<Education>("/educations", payload);
  return response.data;
}

export async function updateEducation(
  educationId: number,
  payload: EducationWritePayload,
): Promise<Education> {
  const response = await api.put<Education>(
    `/educations/${educationId}`,
    payload,
  );

  return response.data;
}

export async function deleteEducation(educationId: number): Promise<void> {
  await api.delete(`/educations/${educationId}`);
}

export async function reorderEducations(
  items: Array<{ id: number; display_order: number }>,
): Promise<void> {
  await api.post("/educations/reorder", { items });
}
