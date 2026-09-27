import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

export default function DisclaimerBanner({ compact = false }) {
  const disclaimerText =
    "This is an academic research and decision-support prototype. The absence of a conflict does NOT guarantee clinical safety. It does NOT provide medical advice or replace a qualified healthcare professional.";

  if (compact) {
    return (
      <div className="bg-amber-50 border-l-4 border-amber-500 p-3 rounded-r text-xs text-amber-900 flex items-start space-x-2">
        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <p className="leading-relaxed font-medium">{disclaimerText}</p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 border border-amber-200 p-4 rounded-lg shadow-sm">
      <div className="flex items-start space-x-3">
        <div className="p-2 bg-amber-100 rounded-full flex-shrink-0 text-amber-700">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div>
          <h4 className="text-sm font-semibold text-amber-950 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <span>Clinical Decision-Support & Academic Prototype Disclaimer</span>
          </h4>
          <p className="text-xs text-amber-900 leading-relaxed font-normal">
            {disclaimerText}
          </p>
        </div>
      </div>
    </div>
  );
}
