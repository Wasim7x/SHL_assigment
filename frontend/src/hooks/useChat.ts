/**
 * Custom hook for managing chat state and interactions.
 */

import { useState, useCallback } from "react";
import { Message, Recommendation, ChatResponse } from "../types";
import { sendChatMessage } from "../api/client";

interface UseChatReturn {
  messages: Message[];
  recommendations: Recommendation[];
  isLoading: boolean;
  isComplete: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  resetConversation: () => void;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading || isComplete) return;

    const userMessage: Message = { role: "user", content: content.trim() };
    const updatedMessages = [...messages, userMessage];

    setMessages(updatedMessages);
    setIsLoading(true);
    setError(null);

    try {
      const response: ChatResponse = await sendChatMessage({
        messages: updatedMessages,
      });

      const assistantMessage: Message = {
        role: "assistant",
        content: response.reply,
      };

      setMessages([...updatedMessages, assistantMessage]);

      if (response.recommendations.length > 0) {
        setRecommendations(response.recommendations);
      }

      if (response.end_of_conversation) {
        setIsComplete(true);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
      // Remove the user message if the request failed
      setMessages(messages);
    } finally {
      setIsLoading(false);
    }
  }, [messages, isLoading, isComplete]);

  const resetConversation = useCallback(() => {
    setMessages([]);
    setRecommendations([]);
    setIsLoading(false);
    setIsComplete(false);
    setError(null);
  }, []);

  return {
    messages,
    recommendations,
    isLoading,
    isComplete,
    error,
    sendMessage,
    resetConversation,
  };
}
