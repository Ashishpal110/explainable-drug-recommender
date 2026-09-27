import React, { useState, useEffect } from 'react';
import { Search, Pill, ChevronLeft, ChevronRight, Filter, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import DisclaimerBanner from '../components/DisclaimerBanner';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getDrugs } from '../services/api';

export default function DrugExplorer() {
  const [drugs, setDrugs] = useState([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(25);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState('');
  const [conditionFilter, setConditionFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDrugList = async (currentOffset = 0) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDrugs({
        search: search.trim() || undefined,
        condition: conditionFilter.trim() || undefined,
        limit,
        offset: currentOffset,
      });
      setDrugs(data.drugs || []);
      setTotal(data.total_drugs || 0);
      setOffset(currentOffset);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDrugList(0);
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchDrugList(0);
  };

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <div className="space-y-6">
      <DisclaimerBanner />

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Pill className="w-5 h-5 text-indigo-600" />
            <span>Indian Medication Catalog Explorer</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Browse and search {total.toLocaleString()} cataloged Indian pharmaceutical formulations, active generic ingredients, indication mappings, and safety rules.
          </p>
        </div>

        {/* Filter Controls */}
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by brand name or active generic..."
              className="w-full pl-9 pr-3.5 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            />
          </div>

          <div className="relative">
            <Filter className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={conditionFilter}
              onChange={(e) => setConditionFilter(e.target.value)}
              placeholder="Filter by indicated condition..."
              className="w-full pl-9 pr-3.5 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            />
          </div>

          <div>
            <button
              type="submit"
              className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              Apply Filter
            </button>
          </div>
        </form>

        {/* Loading / Error States */}
        {loading && <LoadingState message="Querying Indian pharmaceutical database..." />}
        {error && <ErrorState title="Failed to Load Medications" error={error} onRetry={() => fetchDrugList(offset)} />}

        {/* Results Table */}
        {!loading && !error && (
          <div className="space-y-4">
            <div className="overflow-x-auto border border-slate-200 rounded-lg">
              <table className="w-full text-left text-xs text-slate-600 divide-y divide-slate-200">
                <thead className="bg-slate-50 text-slate-700 font-semibold uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-3 px-4">Brand Formulation</th>
                    <th className="py-3 px-4">Generic / Active Salt</th>
                    <th className="py-3 px-4">Pharmacological Class</th>
                    <th className="py-3 px-4 text-center">Avg Rating</th>
                    <th className="py-3 px-4 text-center">Brand Reviews</th>
                    <th className="py-3 px-4 text-center">Positive Ratio</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {drugs.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-400">
                        No medications matched the query criteria.
                      </td>
                    </tr>
                  ) : (
                    drugs.map((drug) => {
                      const hasRev = drug.total_reviews > 0;
                      return (
                        <tr key={drug.drug_id} className="hover:bg-slate-50/75 transition-colors">
                          <td className="py-3 px-4 font-bold text-slate-900">
                            <Link
                              to={`/drugs/${drug.drug_id}`}
                              className="hover:text-indigo-600 transition-colors"
                            >
                              {drug.name}
                            </Link>
                          </td>
                          <td className="py-3 px-4 font-mono text-slate-500 italic">
                            {drug.generic_name || '—'}
                          </td>
                          <td className="py-3 px-4">
                            <span className="px-2 py-0.5 bg-slate-100 rounded text-slate-700 font-medium">
                              {drug.drug_class || 'Unspecified'}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center font-semibold text-slate-800">
                            {hasRev && drug.avg_rating ? `${drug.avg_rating.toFixed(1)}/10` : '—'}
                          </td>
                          <td className="py-3 px-4 text-center text-slate-600 font-medium">
                            {hasRev ? drug.total_reviews.toLocaleString() : '0'}
                          </td>
                          <td className="py-3 px-4 text-center">
                            {hasRev && drug.positive_sentiment_ratio !== null && drug.positive_sentiment_ratio !== undefined ? (
                              <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                                {Math.round(drug.positive_sentiment_ratio * 100)}%
                              </span>
                            ) : (
                              <span className="text-slate-400 font-normal">—</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <Link
                              to={`/drugs/${drug.drug_id}`}
                              className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-900 font-semibold"
                            >
                              <span>Profile</span>
                              <ExternalLink className="w-3 h-3" />
                            </Link>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between text-xs text-slate-500 pt-2">
              <div>
                Showing <span className="font-semibold text-slate-700">{drugs.length ? offset + 1 : 0}</span> to{' '}
                <span className="font-semibold text-slate-700">{Math.min(offset + limit, total)}</span> of{' '}
                <span className="font-semibold text-slate-700">{total.toLocaleString()}</span> medications
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={offset === 0}
                  onClick={() => fetchDrugList(Math.max(0, offset - limit))}
                  className="p-1.5 border border-slate-300 rounded-md hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="px-2 font-medium">
                  Page {currentPage} of {totalPages || 1}
                </span>
                <button
                  type="button"
                  disabled={offset + limit >= total}
                  onClick={() => fetchDrugList(offset + limit)}
                  className="p-1.5 border border-slate-300 rounded-md hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
