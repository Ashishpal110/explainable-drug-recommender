import React from 'react';
import { ShieldCheck, AlertTriangle, ShieldAlert } from 'lucide-react';

/**
 * Safety badge strictly supporting:
 * - NO_KNOWN_CONFLICT (local safety DB check passed, no matching rule found)
 * - WARNING (moderate DDI or precaution)
 * - FILTERED_SAFETY_CONFLICT (critical conflict: allergy, severe DDI, or contraindication)
 */
export default function SafetyBadge({ status, className = '' }) {
  const normStatus = (status || '').toUpperCase();

  switch (normStatus) {
    case 'NO_KNOWN_CONFLICT':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300 ${className}`}
          title="No matching allergy, DDI, or contraindication conflict was found in the local safety knowledge base. (Does not guarantee clinical safety)."
        >
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
          <span>No Known Conflict</span>
        </span>
      );

    case 'WARNING':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-300 ${className}`}
          title="Precaution / Moderate drug interaction detected. Monitoring recommended."
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
          <span>Warning / Precaution</span>
        </span>
      );

    case 'FILTERED_SAFETY_CONFLICT':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-300 ${className}`}
          title="Filtered out due to a high-severity allergy conflict, severe DDI, or absolute contraindication."
        >
          <ShieldAlert className="w-3.5 h-3.5 text-rose-600 flex-shrink-0" />
          <span>Filtered Safety Conflict</span>
        </span>
      );

    default:
      return (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 ${className}`}
        >
          <span>{status || 'Unknown'}</span>
        </span>
      );
  }
}
