import { useChat } from "./hooks/useChat";
import { ChatWindow } from "./components/ChatWindow";
import { ChatInput } from "./components/ChatInput";
import { RecommendationList } from "./components/RecommendationList";

function App() {
  const {
    messages,
    recommendations,
    isLoading,
    isComplete,
    error,
    sendMessage,
    resetConversation,
  } = useChat();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-shl-green rounded flex items-center justify-center">
            <span className="text-white font-bold text-sm">S</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">
              SHL Assessment Recommender
            </h1>
            <p className="text-xs text-gray-500">
              Find the right assessments for your hiring needs
            </p>
          </div>
        </div>
        <button
          onClick={resetConversation}
          className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors"
        >
          New Chat
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        {/* Chat Messages */}
        <ChatWindow messages={messages} isLoading={isLoading} />

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <RecommendationList recommendations={recommendations} />
        )}

        {/* Error Display */}
        {error && (
          <div className="px-4 py-2 mx-4 mb-2 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Input */}
        <ChatInput
          onSend={sendMessage}
          disabled={isLoading || isComplete}
          placeholder={
            isComplete
              ? "Conversation complete — click 'New Chat' to start over"
              : "Describe the role you're hiring for..."
          }
        />
      </main>
    </div>
  );
}

export default App;
