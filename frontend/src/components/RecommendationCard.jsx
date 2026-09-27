import React from 'react';
import { Pill, AlertTriangle, ShieldCheck, ChevronRight, Building2, IndianRupee, Package, FileText, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';
import SafetyBadge from './SafetyBadge';
import FactorBreakdown from './FactorBreakdown';
import ReviewSummary from './ReviewSummary';
import ExplanationPanel from './ExplanationPanel';

/**
 * Recommendation Card representing a clinically screened Indian pharmaceutical candidate.
 * Visual hierarchy prioritizes clinical/safety information, followed by factor contributions,
 * Indian market metadata (composition, manufacturer, INR pricing), and decision explanation.
 */
export default function RecommendationCard({ drug, rank }) {
  if (!drug) return null;

  const {
    drug_id,
    drug_name,
    brand_name,
    generic_name,
    drug_class,
    composition,
    manufacturer,
    dosage_form,
    pack_size,
    price_inr,
    condition,
    evidence_source,
    final_score = 0,
    factors = {},
    review_summary = {},
    safety_status = 'NO_KNOWN_CONFLICT',
    safety_details = {},
    explanation,
  } = drug;

  const finalScorePercent = Math.round(final_score * 100);
  const isWarning = safety_status === 'WARNING';
  const ddiWarnings = safety_details?.ddi_warnings || [];

  const evidenceLevel = factors?.sentiment_evidence_level || 'no_review_evidence';
  const evidenceSourceText = factors?.sentiment_evidence_source;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow p-5 space-y-4">
      {/* 1. Clinical Header: Rank, Brand Name, Generic Constituents, Score, Safety Badge */}
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
            <div className="flex items-center gap-2 mt-1 text-xs text-slate-600 flex-wrap">
              <span className="inline-flex items-center gap-1 font-medium bg-slate-100 px-2 py-0.5 rounded">
                <Pill className="w-3 h-3 text-slate-500" />
                {drug_class || 'Class Unspecified'}
              </span>
              {condition && (
                <span className="inline-flex items-center gap-1 font-medium bg-blue-50 text-blue-800 border border-blue-200 px-2 py-0.5 rounded text-[11px]">
                  <Activity className="w-3 h-3 text-blue-600" />
                  <span>Indication: {condition}</span>
                </span>
              )}
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

      {/* 2. Indication Evidence Source Banner */}
      {evidence_source && (
        <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
          <FileText className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" />
          <span className="font-semibold text-slate-700">Evidence Source:</span>
          <span className="truncate">{evidence_source}</span>
        </div>
      )}

      {/* 3. Sentiment Provenance Callout */}
      <div className="text-xs">
        {evidenceLevel === 'active_ingredient_review' && (
          <div className="p-2.5 bg-emerald-50/60 border border-emerald-200 rounded-lg text-emerald-900 flex items-start gap-2">
            <span className="px-1.5 py-0.5 bg-emerald-200 text-emerald-900 rounded text-[10px] font-bold uppercase tracking-wider flex-shrink-0 mt-0.5">
              Generic Review Data
            </span>
            <p className="leading-relaxed">
              Review evidence is derived from the clinical drug-review corpus for active ingredient <strong>{generic_name}</strong>, not this specific commercial formulation.
            </p>
          </div>
        )}
        {evidenceLevel === 'brand_review' && (
          <div className="p-2.5 bg-blue-50/60 border border-blue-200 rounded-lg text-blue-900 flex items-start gap-2">
            <span className="px-1.5 py-0.5 bg-blue-200 text-blue-900 rounded text-[10px] font-bold uppercase tracking-wider flex-shrink-0 mt-0.5">
              Brand Review Data
            </span>
            <p className="leading-relaxed">
              Based on historical patient reviews recorded directly for this brand name in the review corpus.
            </p>
          </div>
        )}
        {evidenceLevel === 'no_review_evidence' && (
          <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-600 flex items-start gap-2">
            <span className="px-1.5 py-0.5 bg-slate-200 text-slate-700 rounded text-[10px] font-bold uppercase tracking-wider flex-shrink-0 mt-0.5">
              No Review Evidence
            </span>
            <p className="leading-relaxed">
              No empirical patient review data recorded. Recommendation relies dynamically on clinical indication match and symptom profile similarity.
            </p>
          </div>
        )}
      </div>

      {/* 4. Recommendation Factor Contributions */}
      <FactorBreakdown factors={factors} />

      {/* 5. Indian Pharmaceutical Market Metadata */}
      <div className="bg-slate-50/75 border border-slate-200 rounded-lg p-3 text-xs space-y-2">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
          Indian Pharmaceutical Information
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-slate-700">
          {manufacturer && (
            <div>
              <span className="text-[10px] text-slate-400 uppercase block">Manufacturer</span>
              <span className="font-semibold text-slate-800 truncate block flex items-center gap-1" title={manufacturer}>
                <Building2 className="w-3 h-3 text-slate-400" />
                {manufacturer}
              </span>
            </div>
          )}
          {price_inr !== null && price_inr !== undefined && price_inr > 0 ? (
            <div>
              <span className="text-[10px] text-slate-400 uppercase block">Catalog Price</span>
              <span className="font-bold text-slate-900 flex items-center">
                <span>₹{Number(price_inr).toFixed(2)}</span>
                {pack_size && <span className="text-[10px] text-slate-500 font-normal ml-1">({pack_size})</span>}
              </span>
            </div>
          ) : (
            <div>
              <span className="text-[10px] text-slate-400 uppercase block">Catalog Price</span>
              <span className="font-medium text-slate-500">Price on request</span>
            </div>
          )}
          {dosage_form && (
            <div>
              <span className="text-[10px] text-slate-400 uppercase block">Dosage Form</span>
              <span className="font-medium text-slate-800">{dosage_form}</span>
            </div>
          )}
          {composition && (
            <div className="col-span-2 sm:col-span-1">
              <span className="text-[10px] text-slate-400 uppercase block">Composition</span>
              <span className="font-medium text-slate-800 truncate block" title={composition}>
                {composition}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 6. Review Summary (with null checks) */}
      <ReviewSummary reviewSummary={review_summary} sentimentEvidenceLevel={evidenceLevel} />

      {/* 7. Moderate Interaction / Precaution Banner if WARNING */}
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

      {/* 8. Explainability Justification Narrative */}
      <ExplanationPanel explanation={explanation} variant={isWarning ? 'warning' : 'default'} />

      {/* 9. View Drug Details Link */}
      <div className="pt-1 flex justify-end">
        <Link
          to={`/drugs/${drug_id}`}
          className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
        >
          <span>View full Indian catalog profile & safety crosswalk</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}

