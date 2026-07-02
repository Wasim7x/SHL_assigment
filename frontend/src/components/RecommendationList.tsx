import { Recommendation } from "../types";
import { RecommendationCard } from "./RecommendationCard";

interface RecommendationListProps {
  recommendations: Recommendation[];
}

export function RecommendationList({ recommendations }: RecommendationListProps) {
  return (
    <div className="px-4 pb-4">
      <div className="bg-green-50 border border-green-200 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-green-800 mb-3 flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Recommended Assessments ({recommendations.length})
        </h3>
        <div className="grid gap-2">
          {recommendations.map((rec, index) => (
            <RecommendationCard key={index} recommendation={rec} index={index} />
          ))}
        </div>
      </div>
    </div>
  );
}
