import { api } from "../lib/api";
import type {
  Service,
  ServiceListResponse,
  ServicePayload,
  ServiceReorderItem,
} from "../types/service";

export interface ListServicesParams {
  search?: string;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}

export async function getServices(
  params: ListServicesParams = {},
): Promise<ServiceListResponse> {
  const response = await api.get<ServiceListResponse>("/services", {
    params,
  });

  return response.data;
}

export async function createService(payload: ServicePayload): Promise<Service> {
  const response = await api.post<Service>("/services", payload);
  return response.data;
}

export async function updateService(
  serviceId: number,
  payload: ServicePayload,
): Promise<Service> {
  const response = await api.put<Service>(`/services/${serviceId}`, payload);

  return response.data;
}

export async function deleteService(serviceId: number): Promise<void> {
  await api.delete(`/services/${serviceId}`);
}

export async function reorderServices(
  items: ServiceReorderItem[],
): Promise<void> {
  await api.post("/services/reorder", { items });
}
