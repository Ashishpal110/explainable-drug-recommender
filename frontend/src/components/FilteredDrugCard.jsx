import React from 'react';
import { ShieldAlert, AlertOctagon, XCircle, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import SafetyBadge from './SafetyBadge';
import FactorBreakdown from './FactorBreakdown';
import ExplanationPanel from './ExplanationPanel';

/**
 * Filtered Drug Card representing candidate medications filtered out due to safety conflicts.
 * Highlights the exact deterministic rule triggered and clinical contraindications.
 */
export default function FilteredDrugCard({ drug }) {
  if (!drug) return null;

  const {
    drug_id,
    drug_name,
    raw_recommendation_score = 0,
    factors = {},
    safety_status = 'FILTERED_SAFETY_CONFLICT',
    exact_rule_triggered = 'SAFETY_CONFLICT',
    affected_items = [],
    severity = 'HIGH',
    clinical_reason,
    explanation,
  } = drug;

  const rawScorePercent = Math.round(raw_recommendation_score * 100);

  return (
    <div className="bg-rose-50/50 rounded-xl border border-rose-200 p-5 space-y-4 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-rose-200 pb-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-lg font-bold text-slate-900 line-through decoration-rose-500 decoration-2">
              {drug_name}
            </span>
            <SafetyBadge status={safety_status} />
            <span className="px-2 py-0.5 text-xs font-bold uppercase rounded bg-rose-600 text-white tracking-wider">
              {severity} SEVERITY
            </span>
          </div>
          <p className="text-xs text-rose-700 mt-1 font-medium">
            Excluded from safe recommendation list due to active patient safety constraint
          </p>
        </div>

        <div className="text-right">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Raw Match Score (Suppressed)
          </div>
          <div className="text-lg font-bold text-slate-500 line-through">
            {rawScorePercent}
            <span className="text-xs font-normal text-slate-400">/100</span>
          </div>
        </div>
      </div>

      {/* Safety Audit Conflict Box */}
      <div className="bg-white rounded-lg border border-rose-200 p-4 space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-rose-900 uppercase tracking-wide">
          <AlertOctagon className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>Rule Violated: {exact_rule_triggered.replace(/_/g, ' ')}</span>
        </div>

        {affected_items && affected_items.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {affected_items.map((item, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-rose-100 text-rose-800 text-xs font-semibold"
              >
                <XCircle className="w-3 h-3 text-rose-600" />
                {item}
              </span>
            ))}
          </div>
        )}

        {clinical_reason && (
          <p className="text-xs text-rose-800 leading-relaxed pt-1">
            <strong className="font-semibold text-rose-950">Clinical Contraindication:</strong> {clinical_reason}
          </p>
        )}
      </div>

      {/* Factor Breakdown (Shows high match score that was overridden by safety) */}
      <div className="opacity-80">
        <FactorBreakdown factors={factors} showLabels={false} />
      </div>

      {/* Justification Narrative */}
      <ExplanationPanel explanation={explanation} variant="filtered" title="Safety Filter Justification" />

      {drug_id && (
        <div className="pt-1 flex justify-end">
          <Link
            to={`/drugs/${drug_id}`}
            className="inline-flex items-center gap-1 text-xs font-semibold text-rose-700 hover:text-rose-900 transition-colors"
          >
            <span>Inspect drug profile & safety crosswalk</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}
    </div>
  );
}
