import React, { useState } from 'react';
import { MessageSquare, Sparkles, Send, Tag, HelpCircle } from 'lucide-react';
import DisclaimerBanner from '../components/DisclaimerBanner';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { analyzeSentiment } from '../services/api';

export default function SentimentAnalyzer() {
  const [text, setText] = useState(
    'This medication worked wonders for my migraine pain! Within 30 minutes the throbbing stopped completely and I experienced zero adverse effects.'
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const sampleReviews = [
    {
      label: 'Positive Sample',
      text: 'This medication worked wonders for my migraine pain! Within 30 minutes the throbbing stopped completely and I experienced zero adverse effects.',
    },
    {
      label: 'Negative Sample',
      text: 'Terrible experience. Caused severe nausea, extreme dizziness, racing heartbeat, and made my symptoms substantially worse. Had to discontinue immediately.',
    },
    {
      label: 'Neutral / Mixed Sample',
      text: 'Moderately effective for symptom relief, but caused slight drowsiness in the afternoon. Average results overall.',
    },
  ];

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await analyzeSentiment(text.trim());
      setResult(res);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentBadge = (sentiment) => {
    switch (sentiment) {
      case 'Positive':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
            Positive Sentiment
          </span>
        );
      case 'Negative':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300">
            Negative Sentiment
          </span>
        );
      case 'Neutral':
      default:
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-800 border border-slate-300">
            Neutral Sentiment
          </span>
        );
    }
  };

  return (
    <div className="space-y-8">
      <DisclaimerBanner />

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-indigo-600" />
            <span>NLP Review Sentiment Analyzer</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Evaluates unstructured patient review text using the offline-trained TF-IDF + Logistic Regression model with rating-derived proxy supervision.
          </p>
          <div className="mt-2.5 p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600 leading-relaxed">
            <strong>Model Provenance Note:</strong> This NLP sentiment model was trained and evaluated on the project's clinical drug-review corpus. Its classification output reflects general patient satisfaction probability and should not be interpreted as Indian patient sentiment unless the evaluated text originates specifically from Indian clinical contexts.
          </div>
        </div>

        {/* Quick Samples */}
        <div className="space-y-1.5">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Quick Test Examples:
          </span>
          <div className="flex flex-wrap gap-2">
            {sampleReviews.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setText(sample.text);
                  setResult(null);
                }}
                className="px-2.5 py-1 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-medium transition-colors"
              >
                {sample.label}
              </button>
            ))}
          </div>
        </div>

        {/* Review Text Input */}
        <form onSubmit={handleAnalyze} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
              Patient Review Text
            </label>
            <textarea
              rows={4}
              required
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste or write patient-reported medication feedback here..."
              className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none leading-relaxed"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading || !text.trim()}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white font-semibold text-xs rounded-lg shadow-sm transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{loading ? 'Evaluating Sentiment...' : 'Analyze Review Sentiment'}</span>
            </button>
          </div>
        </form>
      </div>

      {loading && <LoadingState message="Vectorizing text and computing class probabilities..." />}

      {error && <ErrorState title="Sentiment Analysis Error" error={error} onRetry={handleAnalyze} />}

      {/* Sentiment Results */}
      {result && !loading && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Predicted Sentiment Classification
              </span>
              <div className="mt-1 flex items-center gap-2">
                {getSentimentBadge(result.predicted_sentiment)}
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div>
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Positive Probability (Polarity)
                </div>
                <div className="text-xl font-bold text-slate-900">
                  {Math.round(result.polarity_score * 100)}%
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Model Confidence
                </div>
                <div className="text-xl font-bold text-indigo-600">
                  {Math.round(result.confidence * 100)}%
                </div>
              </div>
            </div>
          </div>

          {/* Salient Keyword Features */}
          {result.top_keywords && result.top_keywords.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5 text-slate-400" />
                <span>Top Salient TF-IDF Feature N-Grams</span>
              </h4>
              <div className="flex flex-wrap gap-2">
                {result.top_keywords.map((kw, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 bg-indigo-50 border border-indigo-200 text-indigo-800 text-xs font-medium rounded-md font-mono"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
