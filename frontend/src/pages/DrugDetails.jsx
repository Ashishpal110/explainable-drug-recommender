import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Pill, ArrowLeft, ShieldAlert, AlertTriangle, Activity, Star, ThumbsUp, MessageSquare } from 'lucide-react';
import DisclaimerBanner from '../components/DisclaimerBanner';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getDrugDetails } from '../services/api';

export default function DrugDetails() {
  const { drugId } = useParams();
  const [drug, setDrug] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const data = await getDrugDetails(drugId);
        setDrug(data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    }
    if (drugId) {
      loadData();
    }
  }, [drugId]);

  return (
    <div className="space-y-6">
      <DisclaimerBanner />

      <div className="flex items-center gap-2">
        <Link
          to="/drugs"
          className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Medication Catalog</span>
        </Link>
      </div>

      {loading && <LoadingState message="Loading medication clinical profile and safety rules..." />}
      {error && <ErrorState title="Drug Profile Error" error={error} />}

      {!loading && !error && drug && (
        <div className="space-y-6">
          {/* Main Drug Overview Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-black text-slate-900">{drug.name}</h2>
                  <span className="px-2.5 py-1 bg-indigo-50 border border-indigo-200 text-indigo-800 text-xs font-semibold rounded-md">
                    {drug.drug_class || 'Class Unspecified'}
                  </span>
                </div>
                {drug.generic_name && (
                  <p className="text-xs text-slate-500 font-mono italic mt-1">
                    Generic: {drug.generic_name}
                  </p>
                )}
              </div>

              {/* Aggregated Satisfaction Metrics */}
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-lg text-amber-800">
                  <Star className="w-4 h-4 text-amber-500 fill-amber-400" />
                  <div>
                    <div className="text-xs text-slate-400 uppercase font-semibold">Rating</div>
                    <div className="text-sm font-bold">{drug.avg_rating ? `${drug.avg_rating.toFixed(1)}/10` : '—'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg text-emerald-800">
                  <ThumbsUp className="w-4 h-4 text-emerald-600" />
                  <div>
                    <div className="text-xs text-slate-400 uppercase font-semibold">Positive</div>
                    <div className="text-sm font-bold">{Math.round(drug.positive_sentiment_ratio * 100)}%</div>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-slate-700">
                  <MessageSquare className="w-4 h-4 text-slate-500" />
                  <div>
                    <div className="text-xs text-slate-400 uppercase font-semibold">Reviews</div>
                    <div className="text-sm font-bold">{drug.total_reviews.toLocaleString()}</div>
                  </div>
                </div>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              {drug.description}
            </p>
          </div>

          {/* Indicated Conditions */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-600" />
              <span>Cataloged Indication Mappings ({drug.indicated_conditions?.length || 0})</span>
            </h3>

            {drug.indicated_conditions?.length === 0 ? (
              <p className="text-xs text-slate-400">No condition indications mapped in corpus.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {drug.indicated_conditions.map((c) => (
                  <div
                    key={c.condition_id}
                    className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs font-bold text-slate-800">{c.condition_name}</div>
                      <div className="text-[11px] text-slate-500">{c.review_count} patient reviews</div>
                    </div>
                    <div className="text-xs font-semibold text-amber-700">
                      {c.avg_rating ? `${c.avg_rating.toFixed(1)}/10` : '—'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Seeded Safety Knowledge Base Rules */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Allergen Crosswalk & Interactions */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-rose-800 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                <span>Allergy & Interaction Knowledge Base</span>
              </h3>

              <div className="space-y-3">
                <div>
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Recognized Allergen Crosswalk Classes:
                  </h4>
                  {drug.allergy_classes?.length === 0 ? (
                    <p className="text-xs text-slate-500 italic">No allergen class crosswalk rules registered.</p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {drug.allergy_classes.map((cls, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 bg-rose-50 border border-rose-200 text-rose-800 rounded-md text-xs font-semibold"
                        >
                          {cls}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="pt-2 border-t border-slate-100">
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Direct Seeded DDI Rules:
                  </h4>
                  <p className="text-xs text-slate-600">
                    {drug.interaction_count} distinct drug interaction pair rule(s) stored in SQLite knowledge base.
                  </p>
                </div>
              </div>
            </div>

            {/* Contraindications */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-amber-800 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Deterministic Contraindications</span>
              </h3>

              {drug.contraindications?.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No explicit contraindication rules registered.</p>
              ) : (
                <div className="space-y-2.5">
                  {drug.contraindications.map((contra, i) => (
                    <div
                      key={i}
                      className="p-3 bg-amber-50/75 border border-amber-200 rounded-lg text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between font-bold text-amber-900">
                        <span>
                          {contra.type} Contraindication: {contra.trigger}
                        </span>
                        <span className="px-1.5 py-0.5 bg-amber-200 text-amber-900 rounded text-[10px] uppercase">
                          {contra.severity}
                        </span>
                      </div>
                      <p className="text-amber-800 leading-relaxed">{contra.reason}</p>
                      <div className="text-[10px] text-amber-600 font-mono">Source: {contra.source}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
