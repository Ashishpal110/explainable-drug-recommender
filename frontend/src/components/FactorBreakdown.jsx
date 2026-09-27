import React from 'react';
import { Target, Sparkles, HeartPulse, Star, Info, HelpCircle } from 'lucide-react';

/**
 * Transparent factor decomposition panel.
 * Displays the mathematical recommendation factors:
 * 1. Condition Match (Indication evidence)
 * 2. Profile Similarity (Symptom query TF-IDF similarity)
 * 3. Sentiment Evidence (Brand-specific vs Active-ingredient review evidence)
 * 4. Review Rating (Historical rating, or dynamically omitted if unavailable)
 *
 * NOTE: Safety is decoupled and NOT included in recommendation scores.
 */
export default function FactorBreakdown({ factors = {}, showLabels = true }) {
  const condMatch = factors.condition_match !== null && factors.condition_match !== undefined
    ? Math.round(factors.condition_match * 100)
    : null;
  const simScore = factors.similarity_score !== null && factors.similarity_score !== undefined
    ? Math.round(factors.similarity_score * 100)
    : null;

  const hasSentiment = factors.sentiment_data_available !== false && factors.sentiment_score !== null && factors.sentiment_score !== undefined;
  const sentScore = hasSentiment ? Math.round(factors.sentiment_score * 100) : null;

  const hasRating = factors.rating_data_available !== false && factors.rating_score !== null && factors.rating_score !== undefined;
  const ratScore = hasRating ? Math.round(factors.rating_score * 100) : null;

  const evidenceLevel = factors.sentiment_evidence_level || 'no_review_evidence';
  const evidenceSource = factors.sentiment_evidence_source;

  let sentimentLabel = 'Sentiment Evidence';
  let sentimentSubtitle = 'No review evidence';
  if (evidenceLevel === 'brand_review') {
    sentimentLabel = 'Brand Sentiment';
    sentimentSubtitle = 'Brand-specific reviews';
  } else if (evidenceLevel === 'active_ingredient_review') {
    sentimentLabel = 'Generic Sentiment';
    sentimentSubtitle = 'Active-ingredient corpus';
  }

  const factorItems = [
    {
      label: 'Condition Match',
      sublabel: 'Verified Indication',
      value: condMatch,
      displayVal: condMatch !== null ? `${condMatch}%` : 'N/A',
      color: 'bg-blue-500',
      textColor: 'text-blue-700',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      icon: Target,
      tooltip: 'Clinical indication prevalence and official formulary evidence',
      isAvailable: condMatch !== null,
    },
    {
      label: 'Profile Similarity',
      sublabel: 'Symptom Match',
      value: simScore,
      displayVal: simScore !== null ? `${simScore}%` : 'N/A',
      color: 'bg-indigo-500',
      textColor: 'text-indigo-700',
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-200',
      icon: Sparkles,
      tooltip: 'TF-IDF symptom query cosine similarity',
      isAvailable: simScore !== null,
    },
    {
      label: sentimentLabel,
      sublabel: sentimentSubtitle,
      value: sentScore,
      displayVal: sentScore !== null ? `${sentScore}%` : 'Unavailable',
      color: 'bg-emerald-500',
      textColor: sentScore !== null ? 'text-emerald-700' : 'text-slate-400',
      bgColor: sentScore !== null ? 'bg-emerald-50' : 'bg-slate-50',
      borderColor: sentScore !== null ? 'border-emerald-200' : 'border-slate-200',
      icon: HeartPulse,
      tooltip: evidenceSource || (evidenceLevel === 'active_ingredient_review' ? 'Derived from active ingredient reviews in clinical corpus' : 'No review sentiment available'),
      isAvailable: sentScore !== null,
    },
    {
      label: 'Review Rating',
      sublabel: hasRating ? 'Brand Rating' : 'Rating unavailable',
      value: ratScore,
      displayVal: ratScore !== null ? `${ratScore}%` : 'Unavailable',
      color: 'bg-amber-500',
      textColor: ratScore !== null ? 'text-amber-700' : 'text-slate-400',
      bgColor: ratScore !== null ? 'bg-amber-50' : 'bg-slate-50',
      borderColor: ratScore !== null ? 'border-amber-200' : 'border-slate-200',
      icon: Star,
      tooltip: hasRating ? 'Normalized historical rating (1-10 mapped to %)' : 'No historical rating available; score dynamically renormalized across available factors',
      isAvailable: hasRating,
    },
  ];

  return (
    <div className="space-y-2">
      {showLabels && (
        <div className="flex items-center justify-between">
          <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Recommendation Factor Contributions
          </h5>
          <span className="text-[11px] text-slate-400">
            Dynamically renormalized for available evidence
          </span>
        </div>
      )}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {factorItems.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.label}
              className={`p-2.5 rounded-lg border ${item.borderColor} ${item.bgColor} flex flex-col justify-between`}
              title={item.tooltip}
            >
              <div className="flex items-start justify-between text-xs text-slate-600 mb-1">
                <div>
                  <span className="font-medium truncate flex items-center gap-1">
                    <Icon className="w-3.5 h-3.5 opacity-75" />
                    {item.label}
                  </span>
                  <div className="text-[10px] text-slate-400 leading-tight">
                    {item.sublabel}
                  </div>
                </div>
                <span className={`font-bold text-xs ${item.textColor}`}>
                  {item.displayVal}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden mt-1.5">
                <div
                  className={`h-1.5 rounded-full ${item.color} transition-all duration-300`}
                  style={{ width: `${item.isAvailable && item.value !== null ? Math.max(4, item.value) : 0}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

