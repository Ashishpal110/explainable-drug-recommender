import React from 'react';
import { Info, AlertCircle, FileText } from 'lucide-react';

export default function ExplanationPanel({ explanation, title = 'Decision Support Explanation', variant = 'default' }) {
  if (!explanation) return null;

  const isWarning = variant === 'warning';
  const isFiltered = variant === 'filtered';

  const containerClasses = isFiltered
    ? 'bg-rose-50 border-rose-200 text-rose-950'
    : isWarning
    ? 'bg-amber-50 border-amber-200 text-amber-950'
    : 'bg-slate-50 border-slate-200 text-slate-900';

  const iconClasses = isFiltered
    ? 'text-rose-600'
    : isWarning
    ? 'text-amber-600'
    : 'text-sky-600';

  return (
    <div className={`border rounded-lg p-3.5 ${containerClasses} space-y-1.5`}>
      <div className="flex items-center gap-2">
        {isFiltered || isWarning ? (
          <AlertCircle className={`w-4 h-4 flex-shrink-0 ${iconClasses}`} />
        ) : (
          <FileText className={`w-4 h-4 flex-shrink-0 ${iconClasses}`} />
        )}
        <h6 className="text-xs font-semibold uppercase tracking-wider">{title}</h6>
      </div>
      <p className="text-xs leading-relaxed opacity-90 pl-6">{explanation}</p>
    </div>
  );
}
