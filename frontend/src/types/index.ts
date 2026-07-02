/**
 * TypeScript interfaces matching the backend API schema.
 */

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface Recommendation {
  name: string;
  url: string;
  test_type: string;
}

export interface ChatResponse {
  reply: string;
  recommendations: Recommendation[];
  end_of_conversation: boolean;
}

export interface ChatRequest {
  messages: Message[];
}

/** Test type display metadata */
export const TEST_TYPE_INFO: Record<string, { label: string; color: string }> = {
  A: { label: "Ability", color: "bg-blue-100 text-blue-800" },
  B: { label: "Behavioral", color: "bg-orange-100 text-orange-800" },
  C: { label: "Competency", color: "bg-teal-100 text-teal-800" },
  D: { label: "Development", color: "bg-indigo-100 text-indigo-800" },
  E: { label: "Exercise", color: "bg-pink-100 text-pink-800" },
  K: { label: "Knowledge", color: "bg-sky-100 text-sky-800" },
  P: { label: "Personality", color: "bg-purple-100 text-purple-800" },
  S: { label: "Simulation", color: "bg-red-100 text-red-800" },
};
