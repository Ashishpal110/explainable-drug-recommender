import React from 'react';
import { Pill, AlertTriangle, ShieldCheck, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import SafetyBadge from './SafetyBadge';
import FactorBreakdown from './FactorBreakdown';
import ReviewSummary from './ReviewSummary';
import ExplanationPanel from './ExplanationPanel';

/**
 * Recommendation Card representing a clinically screened candidate medication.
 * Safety is decoupled from recommendation scoring.
 */
export default function RecommendationCard({ drug, rank }) {
  if (!drug) return null;

  const {
    drug_id,
    drug_name,
    generic_name,
    drug_class,
    final_score = 0,
    factors = {},
    review_summary = {},
    safety_status = 'NO_KNOWN_CONFLICT',
    safety_details = {},
    explanation,
  } = drug;

  const finalScorePercent = Math.round(final_score * 100);
  const isWarning = safety_status === 'WARNING';
  const ddiWarnings = safety_details.ddi_warnings || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow p-5 space-y-4">
      {/* Header with Rank, Drug Name, Class, Score, Safety Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-start space-x-3">
          {rank !== undefined && (
            <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-700 font-bold text-sm flex-shrink-0">
              #{rank}
            </div>
          )}
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <Link
                to={`/drugs/${drug_id}`}
                className="text-lg font-bold text-slate-900 hover:text-indigo-600 transition-colors"
              >
                {drug_name}
              </Link>
              {generic_name && (
                <span className="text-xs text-slate-500 font-mono italic">
                  ({generic_name})
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1 text-xs text-slate-600">
              <span className="inline-flex items-center gap-1 font-medium bg-slate-100 px-2 py-0.5 rounded">
                <Pill className="w-3 h-3 text-slate-500" />
                {drug_class || 'Class Unspecified'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          <SafetyBadge status={safety_status} />
          <div className="text-right">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Recommendation Score
            </div>
            <div className="text-xl font-black text-indigo-600">
              {finalScorePercent}
              <span className="text-xs font-medium text-slate-500">/100</span>
            </div>
          </div>
        </div>
      </div>

      {/* Review Statistics */}
      <ReviewSummary reviewSummary={review_summary} />

      {/* 4-Factor Recommendation Breakdown (Safety Decoupled) */}
      <FactorBreakdown factors={factors} />

      {/* Moderate Interaction / Precaution Banner if WARNING */}
      {isWarning && ddiWarnings.length > 0 && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 space-y-1">
          <div className="font-semibold flex items-center gap-1.5 text-amber-800">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>Moderate Interaction Alert:</span>
          </div>
          {ddiWarnings.map((ddi, i) => (
            <p key={i} className="pl-5 text-amber-800">
              • With <strong className="font-semibold">{ddi.interacting_drug_name}</strong>: {ddi.interaction_mechanism} ({ddi.clinical_action})
            </p>
          ))}
        </div>
      )}

      {/* Explainability Justification Narrative */}
      <ExplanationPanel explanation={explanation} variant={isWarning ? 'warning' : 'default'} />

      {/* View Drug Details Link */}
      <div className="pt-1 flex justify-end">
        <Link
          to={`/drugs/${drug_id}`}
          className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
        >
          <span>View catalog profile & full safety rules</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}
