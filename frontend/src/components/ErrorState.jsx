import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default function ErrorState({ title = 'Error Loading Data', error, onRetry }) {
  const errorMsg = typeof error === 'string' ? error : error?.message || 'An unexpected error occurred while communicating with the backend.';

  return (
    <div className="bg-rose-50 border border-rose-200 rounded-xl p-8 text-center shadow-sm space-y-4 max-w-xl mx-auto">
      <div className="w-12 h-12 rounded-full bg-rose-100 flex items-center justify-center mx-auto text-rose-600">
        <AlertCircle className="w-6 h-6" />
      </div>
      <div>
        <h3 className="text-base font-semibold text-rose-950">{title}</h3>
        <p className="text-xs text-rose-800 mt-1 max-w-md mx-auto">{errorMsg}</p>
      </div>

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Operation</span>
        </button>
      )}
    </div>
  );
}
