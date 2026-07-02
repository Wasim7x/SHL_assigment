import { Recommendation, TEST_TYPE_INFO } from "../types";

interface RecommendationCardProps {
  recommendation: Recommendation;
  index: number;
}

export function RecommendationCard({ recommendation, index }: RecommendationCardProps) {
  const typeInfo = TEST_TYPE_INFO[recommendation.test_type] || {
    label: recommendation.test_type,
    color: "bg-gray-100 text-gray-800",
  };

  return (
    <div className="flex items-center justify-between bg-white rounded-lg px-4 py-3 border border-gray-100 hover:border-green-300 transition-colors">
      <div className="flex items-center gap-3">
        <span className="text-xs font-medium text-gray-400 w-5">
          {index + 1}.
        </span>
        <div>
          <p className="text-sm font-medium text-gray-900">
            {recommendation.name}
          </p>
          <span
            className={`inline-block mt-1 px-2 py-0.5 text-xs font-medium rounded-full ${typeInfo.color}`}
          >
            {typeInfo.label}
          </span>
        </div>
      </div>
      <a
        href={recommendation.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs px-3 py-1.5 bg-shl-green/10 text-shl-green font-medium rounded-md hover:bg-shl-green/20 transition-colors whitespace-nowrap"
      >
        View on SHL →
      </a>
    </div>
  );
}
