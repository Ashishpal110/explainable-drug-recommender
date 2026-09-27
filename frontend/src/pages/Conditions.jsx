import React, { useState, useEffect } from 'react';
import { Activity, Search, Pill } from 'lucide-react';
import DisclaimerBanner from '../components/DisclaimerBanner';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getConditions } from '../services/api';

export default function Conditions() {
  const [conditions, setConditions] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadConditions() {
      setLoading(true);
      setError(null);
      try {
        const data = await getConditions();
        setConditions(data.conditions || []);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    }
    loadConditions();
  }, []);

  const filtered = conditions.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    (c.category && c.category.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <DisclaimerBanner />

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-600" />
              <span>Medical Conditions Index</span>
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Indexed medical indications cataloged from the Drugs.com review corpus.
            </p>
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter conditions by name..."
              className="w-full pl-9 pr-3.5 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            />
          </div>
        </div>

        {loading && <LoadingState message="Loading medical conditions catalog..." />}
        {error && <ErrorState title="Failed to Load Conditions" error={error} />}

        {!loading && !error && (
          <div className="space-y-3">
            <div className="text-xs text-slate-500 font-medium">
              Showing {filtered.length} of {conditions.length} cataloged conditions
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {filtered.map((c) => (
                <div
                  key={c.condition_id}
                  className="p-3.5 bg-slate-50/75 hover:bg-indigo-50/50 border border-slate-200 hover:border-indigo-200 rounded-lg transition-all space-y-1.5"
                >
                  <div className="font-bold text-xs text-slate-900 truncate" title={c.name}>
                    {c.name}
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span className="px-1.5 py-0.5 bg-slate-200/70 text-slate-700 rounded text-[10px] font-medium">
                      {c.category || 'General'}
                    </span>
                    <span className="flex items-center gap-1 font-semibold text-indigo-600">
                      <Pill className="w-3 h-3" />
                      {c.drug_count} drugs
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
