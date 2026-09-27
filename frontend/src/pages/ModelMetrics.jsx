import React, { useState, useEffect } from 'react';
import { BarChart3, CheckCircle2, Clock, Database, Layers, BrainCircuit } from 'lucide-react';
import DisclaimerBanner from '../components/DisclaimerBanner';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getModelMetrics } from '../services/api';

export default function ModelMetrics() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadMetrics() {
      setLoading(true);
      setError(null);
      try {
        const data = await getModelMetrics();
        setMetrics(data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, []);

  const sentimentData = metrics?.sentiment_model;
  const isEvaluated = metrics?.model_evaluated;

  return (
    <div className="space-y-6">
      <DisclaimerBanner />

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            <span>Review Sentiment Classification — Holdout Evaluation</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Empirical offline evaluation metrics for the NLP review sentiment classifier on the holdout test set (53,200 reviews).
          </p>
          <div className="mt-2.5 p-2.5 bg-indigo-50/60 border border-indigo-200 rounded-lg text-xs text-indigo-900 leading-relaxed">
            <strong>Architecture Clarification:</strong> These metrics evaluate the accuracy of NLP sentiment polarity extraction from unstructured patient reviews. The recommendation engine integrates this sentiment signal with clinical condition matching, TF-IDF symptom profile similarity, and deterministic safety constraint screening across the 245,644-entry Indian pharmaceutical catalog.
          </div>
        </div>

        {loading && <LoadingState message="Loading empirical model metrics from evaluation report..." />}
        {error && <ErrorState title="Failed to Load Model Metrics" error={error} />}

        {!loading && !error && !isEvaluated && (
          <div className="p-8 bg-slate-50 border border-slate-200 rounded-xl text-center text-xs text-slate-500">
            Model evaluation has not yet been executed. Run offline training and evaluation script.
          </div>
        )}

        {!loading && !error && isEvaluated && sentimentData && (
          <div className="space-y-8">
            {/* Top Stat Summary Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-xl">
                <div className="text-xs font-semibold uppercase tracking-wider text-indigo-700">
                  Sentiment Accuracy
                </div>
                <div className="text-2xl font-black text-indigo-900 mt-1">
                  {(sentimentData.accuracy * 100).toFixed(2)}%
                </div>
                <div className="text-[11px] text-indigo-600 mt-0.5">53,200 holdout reviews</div>
              </div>

              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                <div className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
                  Macro F1-Score
                </div>
                <div className="text-2xl font-black text-emerald-900 mt-1">
                  {sentimentData.f1_macro?.toFixed(4)}
                </div>
                <div className="text-[11px] text-emerald-600 mt-0.5">Unweighted 3-class mean</div>
              </div>

              <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
                <div className="text-xs font-semibold uppercase tracking-wider text-blue-700">
                  Weighted F1-Score
                </div>
                <div className="text-2xl font-black text-blue-900 mt-1">
                  {sentimentData.f1_weighted?.toFixed(4)}
                </div>
                <div className="text-[11px] text-blue-600 mt-0.5">Support-weighted score</div>
              </div>

              <div className="p-4 bg-purple-50 border border-purple-200 rounded-xl">
                <div className="text-xs font-semibold uppercase tracking-wider text-purple-700">
                  Macro Recall
                </div>
                <div className="text-2xl font-black text-purple-900 mt-1">
                  {sentimentData.recall_macro?.toFixed(4)}
                </div>
                <div className="text-[11px] text-purple-600 mt-0.5">Balanced class sensitivity</div>
              </div>
            </div>

            {/* Model & Dataset Metadata */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <BrainCircuit className="w-4 h-4 text-indigo-600" />
                <span>Model Pipeline Specifications</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-slate-600">
                <div>
                  <strong className="font-semibold text-slate-800">Model Name:</strong> {sentimentData.model_name}
                </div>
                <div>
                  <strong className="font-semibold text-slate-800">Classifier:</strong> {sentimentData.classifier}
                </div>
                <div>
                  <strong className="font-semibold text-slate-800">Feature Vectorizer:</strong> {sentimentData.vectorizer}
                </div>
                <div>
                  <strong className="font-semibold text-slate-800">Supervision Strategy:</strong> {sentimentData.supervision_method}
                </div>
                <div>
                  <strong className="font-semibold text-slate-800">Training Samples:</strong> {sentimentData.train_samples?.toLocaleString()} reviews
                </div>
                <div>
                  <strong className="font-semibold text-slate-800">Training Duration:</strong> {sentimentData.training_time_seconds}s
                </div>
              </div>
            </div>

            {/* Per-Class Evaluation Metrics */}
            {sentimentData.per_class_metrics && (
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <Layers className="w-4 h-4 text-indigo-600" />
                  <span>Per-Class Classification Metrics (Holdout Test Split)</span>
                </h3>
                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left text-xs text-slate-600 divide-y divide-slate-200">
                    <thead className="bg-slate-50 text-slate-700 font-semibold uppercase tracking-wider text-[11px]">
                      <tr>
                        <th className="py-2.5 px-4">Sentiment Class</th>
                        <th className="py-2.5 px-4 text-center">Precision</th>
                        <th className="py-2.5 px-4 text-center">Recall</th>
                        <th className="py-2.5 px-4 text-center">F1-Score</th>
                        <th className="py-2.5 px-4 text-right">Holdout Support</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {Object.entries(sentimentData.per_class_metrics).map(([cls, row]) => (
                        <tr key={cls}>
                          <td className="py-2.5 px-4 font-bold text-slate-900">{cls}</td>
                          <td className="py-2.5 px-4 text-center font-mono">{(row.precision * 100).toFixed(2)}%</td>
                          <td className="py-2.5 px-4 text-center font-mono">{(row.recall * 100).toFixed(2)}%</td>
                          <td className="py-2.5 px-4 text-center font-mono font-semibold text-indigo-700">
                            {row['f1-score']?.toFixed(4)}
                          </td>
                          <td className="py-2.5 px-4 text-right font-mono">{row.support?.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Confusion Matrix */}
            {sentimentData.confusion_matrix && (
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                  <span>Holdout Test Confusion Matrix</span>
                </h3>
                <div className="overflow-x-auto border border-slate-200 rounded-lg p-4 bg-slate-50">
                  <table className="w-full max-w-lg mx-auto text-center text-xs text-slate-700 border-collapse">
                    <thead>
                      <tr>
                        <th className="p-2"></th>
                        <th colSpan={3} className="p-2 font-bold uppercase tracking-wider text-[11px] text-slate-600 border-b border-slate-300">
                          Predicted Sentiment
                        </th>
                      </tr>
                      <tr className="text-slate-500 font-semibold">
                        <th className="p-2 text-left">Actual</th>
                        {sentimentData.confusion_matrix.labels.map((lbl) => (
                          <th key={lbl} className="p-2 font-mono">{lbl}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sentimentData.confusion_matrix.matrix.map((row, i) => (
                        <tr key={i} className="border-t border-slate-200">
                          <td className="p-2 text-left font-bold text-slate-900 font-mono">
                            {sentimentData.confusion_matrix.labels[i]}
                          </td>
                          {row.map((cell, j) => {
                            const isDiagonal = i === j;
                            return (
                              <td
                                key={j}
                                className={`p-2.5 font-mono font-semibold ${
                                  isDiagonal
                                    ? 'bg-emerald-100 text-emerald-900 rounded'
                                    : 'text-slate-600'
                                }`}
                              >
                                {cell.toLocaleString()}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
