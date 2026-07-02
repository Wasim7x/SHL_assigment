import { useEffect, useRef } from "react";
import { Message } from "../types";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
}

export function ChatWindow({ messages, isLoading }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 chat-scroll">
      {messages.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-shl-green/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-shl-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h2 className="text-xl font-medium text-gray-900 mb-2">
            Hi! I'm your SHL Assessment Advisor.
          </h2>
          <p className="text-gray-500 max-w-md mx-auto">
            Tell me about the role you're hiring for, and I'll recommend the most
            relevant SHL assessments. You can describe the job, specify skills to
            test, or ask me to compare assessments.
          </p>
          <div className="mt-6 flex flex-wrap gap-2 justify-center">
            {[
              "Hiring a Java developer",
              "Need personality tests for managers",
              "Assess customer service skills",
            ].map((suggestion) => (
              <button
                key={suggestion}
                className="px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-full hover:bg-gray-50 text-gray-700 transition-colors"
                onClick={() => {
                  // This would need to be passed as a prop for full functionality
                  const event = new CustomEvent("suggestion-click", {
                    detail: suggestion,
                  });
                  window.dispatchEvent(event);
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {messages.map((message, index) => (
        <MessageBubble key={index} message={message} />
      ))}

      {isLoading && <TypingIndicator />}

      <div ref={bottomRef} />
    </div>
  );
}
