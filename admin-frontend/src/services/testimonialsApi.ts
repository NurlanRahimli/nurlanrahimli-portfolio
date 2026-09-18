import { api } from "../lib/api";
import type {
  Testimonial,
  TestimonialList,
  TestimonialWritePayload,
} from "../types/testimonial";

export interface ListTestimonialsParams {
  search?: string;
  isActive?: boolean;
  limit?: number;
  offset?: number;
}

export async function listTestimonials({
  search,
  isActive,
  limit = 100,
  offset = 0,
}: ListTestimonialsParams = {}): Promise<TestimonialList> {
  const response = await api.get<TestimonialList>("/testimonials", {
    params: {
      search: search?.trim() || undefined,
      is_active: isActive,
      limit,
      offset,
    },
  });

  return response.data;
}

export async function createTestimonial(
  payload: TestimonialWritePayload,
): Promise<Testimonial> {
  const response = await api.post<Testimonial>("/testimonials", payload);
  return response.data;
}

export async function updateTestimonial(
  testimonialId: number,
  payload: TestimonialWritePayload,
): Promise<Testimonial> {
  const response = await api.put<Testimonial>(
    `/testimonials/${testimonialId}`,
    payload,
  );
  return response.data;
}

export async function deleteTestimonial(testimonialId: number): Promise<void> {
  await api.delete(`/testimonials/${testimonialId}`);
}

export async function reorderTestimonials(
  items: Array<{ id: number; display_order: number }>,
): Promise<void> {
  await api.post("/testimonials/reorder", { items });
}
