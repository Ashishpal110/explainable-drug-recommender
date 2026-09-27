import React from 'react';
import { Star, ThumbsUp, MessageSquare } from 'lucide-react';

export default function ReviewSummary({ reviewSummary = {} }) {
  const posRatio = Math.round((reviewSummary.positive_ratio || 0) * 100);
  const totalReviews = reviewSummary.total_reviews || 0;
  const avgRating = Number(reviewSummary.average_rating || 0).toFixed(1);

  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
      <div className="flex items-center gap-1 bg-amber-50 text-amber-800 px-2.5 py-1 rounded border border-amber-200">
        <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-400" />
        <span className="font-semibold">{avgRating}</span>
        <span className="text-slate-400">/10</span>
      </div>

      <div className="flex items-center gap-1 bg-emerald-50 text-emerald-800 px-2.5 py-1 rounded border border-emerald-200">
        <ThumbsUp className="w-3.5 h-3.5 text-emerald-600" />
        <span className="font-semibold">{posRatio}%</span>
        <span>Positive</span>
      </div>

      <div className="flex items-center gap-1 bg-slate-50 text-slate-700 px-2.5 py-1 rounded border border-slate-200">
        <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
        <span className="font-medium">{totalReviews.toLocaleString()}</span>
        <span>Reviews</span>
      </div>
    </div>
  );
}
