import React from 'react';
import { AlertTriangle, ShieldCheck, Info } from 'lucide-react';

export default function DisclaimerBanner({ compact = false }) {
  const primaryDisclaimer =
    "This system is an academic research and clinical decision-support prototype. It does not replace a qualified medical professional, provide formal medical diagnoses, or prescribe medications. The absence of an alert does not guarantee clinical safety.";
  const provenanceDisclaimer =
    "Indian pharmaceutical catalog listings, clinical indication mappings, and patient review-derived sentiment evidence originate from distinct sources and are explicitly labeled by provenance.";

  if (compact) {
    return (
      <div className="bg-amber-50 border-l-4 border-amber-500 p-3 rounded-r text-xs text-amber-900 flex items-start space-x-2">
        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <p className="leading-relaxed font-medium">{primaryDisclaimer}</p>
          <p className="text-[11px] text-amber-800 leading-relaxed">{provenanceDisclaimer}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 border border-amber-200 p-4 rounded-xl shadow-sm space-y-2">
      <div className="flex items-start space-x-3">
        <div className="p-2 bg-amber-100 rounded-lg flex-shrink-0 text-amber-700 mt-0.5">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h4 className="text-xs font-bold text-amber-950 uppercase tracking-wider flex items-center gap-1.5">
            <span>Academic Decision-Support Prototype & Data Provenance Notice</span>
          </h4>
          <p className="text-xs text-amber-900 leading-relaxed">
            {primaryDisclaimer}
          </p>
          <p className="text-[11px] text-amber-800 leading-relaxed pt-0.5 border-t border-amber-200/60">
            {provenanceDisclaimer}
          </p>
        </div>
      </div>
    </div>
  );
}

