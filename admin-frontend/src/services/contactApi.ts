import { api } from "../lib/api";
import type { ContactContent, ContactContentPayload } from "../types/contact";

export async function getContactContent(): Promise<ContactContent | null> {
  const response = await api.get<ContactContent | null>("/contact");
  return response.data;
}

export async function updateContactContent(
  payload: ContactContentPayload,
): Promise<ContactContent> {
  const response = await api.put<ContactContent>("/contact", payload);
  return response.data;
}
