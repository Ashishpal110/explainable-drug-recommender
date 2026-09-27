import React from 'react';
import { Star, ThumbsUp, MessageSquare, Info } from 'lucide-react';

export default function ReviewSummary({ reviewSummary = {}, sentimentEvidenceLevel = null }) {
  const totalReviews = reviewSummary?.total_reviews || 0;
  const avgRating = reviewSummary?.average_rating !== null && reviewSummary?.average_rating !== undefined
    ? Number(reviewSummary.average_rating).toFixed(1)
    : null;
  const posRatio = reviewSummary?.positive_ratio !== null && reviewSummary?.positive_ratio !== undefined
    ? Math.round(reviewSummary.positive_ratio * 100)
    : null;

  // Case 1: Active ingredient review evidence with 0 brand reviews
  if (totalReviews === 0) {
    return (
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <div className="flex items-center gap-1.5 bg-slate-100 text-slate-600 px-2.5 py-1 rounded border border-slate-200">
          <MessageSquare className="w-3.5 h-3.5 text-slate-400" />
          <span>No brand-specific reviews recorded</span>
        </div>
        <div className="flex items-center gap-1.5 bg-slate-100 text-slate-500 px-2.5 py-1 rounded border border-slate-200">
          <Star className="w-3.5 h-3.5 text-slate-400" />
          <span>Rating data unavailable</span>
        </div>
      </div>
    );
  }

  // Case 2: Brand reviews exist
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
      {avgRating !== null ? (
        <div className="flex items-center gap-1 bg-amber-50 text-amber-800 px-2.5 py-1 rounded border border-amber-200">
          <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-400" />
          <span className="font-semibold">{avgRating}</span>
          <span className="text-slate-400">/10</span>
        </div>
      ) : (
        <div className="flex items-center gap-1 bg-slate-100 text-slate-500 px-2.5 py-1 rounded border border-slate-200">
          <Star className="w-3.5 h-3.5 text-slate-400" />
          <span>Rating unavailable</span>
        </div>
      )}

      {posRatio !== null && (
        <div className="flex items-center gap-1 bg-emerald-50 text-emerald-800 px-2.5 py-1 rounded border border-emerald-200">
          <ThumbsUp className="w-3.5 h-3.5 text-emerald-600" />
          <span className="font-semibold">{posRatio}%</span>
          <span>Positive</span>
        </div>
      )}

      <div className="flex items-center gap-1 bg-slate-50 text-slate-700 px-2.5 py-1 rounded border border-slate-200">
        <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
        <span className="font-medium">{totalReviews.toLocaleString()}</span>
        <span>Brand Reviews</span>
      </div>
    </div>
  );
}

