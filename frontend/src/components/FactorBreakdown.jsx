import React from 'react';
import { Target, Sparkles, HeartPulse, Star } from 'lucide-react';

/**
 * Transparent factor decomposition panel.
 * Displays only the 4 mathematical recommendation factors:
 * 1. Condition Match
 * 2. Similarity Score
 * 3. Sentiment Score
 * 4. Rating Score
 *
 * NOTE: Safety is decoupled and NOT included in these factors.
 */
export default function FactorBreakdown({ factors = {}, showLabels = true }) {
  const condMatch = Math.round((factors.condition_match || 0) * 100);
  const simScore = Math.round((factors.similarity_score || 0) * 100);
  const sentScore = Math.round((factors.sentiment_score || 0) * 100);
  const ratScore = Math.round((factors.rating_score || 0) * 100);

  const factorItems = [
    {
      label: 'Condition Match',
      value: condMatch,
      color: 'bg-blue-500',
      textColor: 'text-blue-700',
      bgColor: 'bg-blue-50',
      icon: Target,
      tooltip: 'Indication prevalence & evidence volume for condition',
    },
    {
      label: 'Profile Similarity',
      value: simScore,
      color: 'bg-indigo-500',
      textColor: 'text-indigo-700',
      bgColor: 'bg-indigo-50',
      icon: Sparkles,
      tooltip: 'TF-IDF cosine similarity with reported symptom query',
    },
    {
      label: 'Patient Sentiment',
      value: sentScore,
      color: 'bg-emerald-500',
      textColor: 'text-emerald-700',
      bgColor: 'bg-emerald-50',
      icon: HeartPulse,
      tooltip: 'NLP model-inferred probability of positive patient satisfaction',
    },
    {
      label: 'Review Rating',
      value: ratScore,
      color: 'bg-amber-500',
      textColor: 'text-amber-700',
      bgColor: 'bg-amber-50',
      icon: Star,
      tooltip: 'Normalized historical patient rating (1-10 mapped to %)',
    },
  ];

  return (
    <div className="space-y-3">
      {showLabels && (
        <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
          Recommendation Factor Contributions
        </h5>
      )}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {factorItems.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.label}
              className={`p-2.5 rounded-lg border border-slate-200 ${item.bgColor} flex flex-col justify-between`}
              title={item.tooltip}
            >
              <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
                <span className="font-medium truncate flex items-center gap-1">
                  <Icon className="w-3.5 h-3.5 opacity-75" />
                  {item.label}
                </span>
                <span className={`font-bold ${item.textColor}`}>{item.value}%</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-1.5 rounded-full ${item.color} transition-all duration-300`}
                  style={{ width: `${Math.max(4, item.value)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
