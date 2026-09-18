import { api } from "../lib/api";
import type {
  Project,
  ProjectList,
  ProjectVideoUploadResponse,
  ProjectWritePayload,
} from "../types/project";

export interface ListProjectsParams {
  search?: string;
  isPublished?: boolean;
  isFeatured?: boolean;
  limit?: number;
  offset?: number;
}

export async function listProjects({
  search,
  isPublished,
  isFeatured,
  limit = 100,
  offset = 0,
}: ListProjectsParams = {}): Promise<ProjectList> {
  const response = await api.get<ProjectList>("/projects", {
    params: {
      search: search?.trim() || undefined,
      is_published: isPublished,
      is_featured: isFeatured,
      limit,
      offset,
    },
  });

  return response.data;
}

export async function getProject(projectId: number): Promise<Project> {
  const response = await api.get<Project>(`/projects/${projectId}`);
  return response.data;
}

export async function createProject(
  payload: ProjectWritePayload,
): Promise<Project> {
  const response = await api.post<Project>("/projects", payload);
  return response.data;
}

export async function updateProject(
  projectId: number,
  payload: ProjectWritePayload,
): Promise<Project> {
  const response = await api.put<Project>(`/projects/${projectId}`, payload);
  return response.data;
}

export async function reorderProjects(
  items: Array<{ id: number; display_order: number }>,
): Promise<void> {
  await api.put("/projects/reorder/all", { items });
}

export async function deleteProject(projectId: number): Promise<void> {
  await api.delete(`/projects/${projectId}`);
}

export async function createProjectVideoUpload(
  projectId: number,
  originalFilename: string,
): Promise<ProjectVideoUploadResponse> {
  const response = await api.post<ProjectVideoUploadResponse>(
    `/projects/${projectId}/video/upload`,
    { original_filename: originalFilename },
  );

  return response.data;
}

export async function deleteProjectVideo(projectId: number): Promise<void> {
  await api.delete(`/projects/${projectId}/video`);
}
