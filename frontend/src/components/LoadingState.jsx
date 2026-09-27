import React from 'react';
import { Loader2, Shield } from 'lucide-react';

export default function LoadingState({ message = 'Auditing candidate drugs and evaluating safety rules...' }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm space-y-4">
      <div className="relative inline-flex items-center justify-center">
        <div className="w-16 h-16 rounded-full bg-indigo-50 border-2 border-indigo-100 flex items-center justify-center">
          <Shield className="w-8 h-8 text-indigo-400" />
        </div>
        <Loader2 className="w-16 h-16 text-indigo-600 animate-spin absolute" />
      </div>
      <div>
        <h3 className="text-base font-semibold text-slate-800">Processing Request</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">{message}</p>
      </div>

      {/* Placeholder Skeletons */}
      <div className="max-w-xl mx-auto space-y-2.5 pt-4 opacity-50">
        <div className="h-4 bg-slate-200 rounded animate-pulse w-3/4 mx-auto" />
        <div className="h-4 bg-slate-200 rounded animate-pulse w-1/2 mx-auto" />
      </div>
    </div>
  );
}
