import { api } from "../lib/api";
import type { AboutContent, AboutContentPayload } from "../types/about";

export async function getAboutContent(): Promise<AboutContent | null> {
  const response = await api.get<AboutContent | null>("/about");
  return response.data;
}

export async function updateAboutContent(
  payload: AboutContentPayload,
): Promise<AboutContent> {
  const response = await api.put<AboutContent>("/about", payload);
  return response.data;
}
