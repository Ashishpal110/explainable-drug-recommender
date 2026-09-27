import React, { useState, useEffect } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertOctagon,
  HelpCircle,
  ShieldCheck,
  FilterX,
  FileCheck2,
} from 'lucide-react';
import PatientProfileForm from '../components/PatientProfileForm';
import RecommendationCard from '../components/RecommendationCard';
import FilteredDrugCard from '../components/FilteredDrugCard';
import DisclaimerBanner from '../components/DisclaimerBanner';
import LoadingState from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import { getConditions, getAllergies, getRecommendations } from '../services/api';

// Explicit Dashboard Request States
const STATES = {
  IDLE: 'IDLE',
  LOADING: 'LOADING',
  SUCCESS: 'SUCCESS',
  ERROR: 'ERROR',
};

export default function Dashboard() {
  const [conditions, setConditions] = useState([]);
  const [allergies, setAllergies] = useState([]);
  const [metadataLoading, setMetadataLoading] = useState(true);
  const [metadataError, setMetadataError] = useState(null);

  const [requestState, setRequestState] = useState(STATES.IDLE);
  const [lastSubmittedProfile, setLastSubmittedProfile] = useState(null);
  const [results, setResults] = useState(null);
  const [apiError, setApiError] = useState(null);

  const loadMetadata = async () => {
    setMetadataLoading(true);
    setMetadataError(null);
    try {
      const [condRes, algRes] = await Promise.all([getConditions(), getAllergies()]);
      setConditions(condRes.conditions || []);
      setAllergies(algRes.allergen_classes || []);
    } catch (err) {
      console.warn('Metadata pre-fetch warning:', err);
      setMetadataError('Could not pre-load conditions and allergy classes from backend.');
    } finally {
      setMetadataLoading(false);
    }
  };

  useEffect(() => {
    loadMetadata();
  }, []);

  const handleProfileSubmit = async (profileData) => {
    if (requestState === STATES.LOADING) return;

    setRequestState(STATES.LOADING);
    setApiError(null);
    setLastSubmittedProfile(profileData);

    try {
      const response = await getRecommendations(profileData);
      setResults(response);
      setRequestState(STATES.SUCCESS);
    } catch (err) {
      setApiError(err.message || 'An error occurred while communicating with the recommendation engine.');
      setRequestState(STATES.ERROR);
    }
  };

  const handleRetry = () => {
    if (lastSubmittedProfile) {
      handleProfileSubmit(lastSubmittedProfile);
    } else {
      setRequestState(STATES.IDLE);
      setApiError(null);
    }
  };

  const recommendedList = results?.recommended_drugs || [];
  const filteredList = results?.filtered_drugs || [];
  const patientSummary = results?.patient_summary;

  return (
    <div className="space-y-8">
      {/* Persistent Educational Disclaimer */}
      <DisclaimerBanner />

      {/* Patient Profile Intake & Audit Form */}
      <PatientProfileForm
        onSubmit={handleProfileSubmit}
        loading={requestState === STATES.LOADING}
        availableConditions={conditions}
        availableAllergies={allergies}
      />

      {/* LOADING STATE */}
      {requestState === STATES.LOADING && (
        <LoadingState message="Retrieving indication matches, calculating profile similarity & patient review sentiment, and executing deterministic safety audits against allergies and DDIs..." />
      )}

      {/* ERROR STATE */}
      {requestState === STATES.ERROR && (
        <ErrorState
          title="Recommendation Service Error"
          error={apiError}
          onRetry={handleRetry}
        />
      )}

      {/* SUCCESS STATE */}
      {requestState === STATES.SUCCESS && results && (
        <div className="space-y-8">
          {/* Patient Query & Screening Summary Header */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FileCheck2 className="w-5 h-5 text-indigo-600" />
                  <span>Clinical Decision Support Output for {patientSummary?.condition}</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Patient Age: <strong className="text-slate-700">{patientSummary?.age} yrs</strong>
                  {patientSummary?.allergies?.length > 0 && (
                    <span> • Allergies: <strong className="text-rose-700">{patientSummary.allergies.join(', ')}</strong></span>
                  )}
                  {patientSummary?.current_medications?.length > 0 && (
                    <span> • Active Meds: <strong className="text-indigo-700">{patientSummary.current_medications.join(', ')}</strong></span>
                  )}
                </p>
              </div>

              {/* Status Pill */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-semibold rounded-lg">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Independent Safety Screening Active</span>
                </span>
              </div>
            </div>

            {/* Quick Metrics Bar */}
            <div className="flex flex-wrap items-center gap-6 text-xs text-slate-600">
              <div>
                <span>Screened Candidates Approved: </span>
                <strong className="text-emerald-700 font-bold">{recommendedList.length}</strong>
              </div>
              <div>
                <span>Excluded Due to Safety Conflicts: </span>
                <strong className="text-rose-700 font-bold">{filteredList.length}</strong>
              </div>
              <div>
                <span>Total Indication Candidates Evaluated: </span>
                <strong className="text-slate-800 font-bold">{recommendedList.length + filteredList.length}</strong>
              </div>
            </div>
          </div>

          {/* 1. RECOMMENDED CANDIDATES SECTION */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Recommended Medications ({recommendedList.length})</span>
              </h3>
              <span className="text-xs text-slate-500">
                Ranked by Multi-Factor Score (Condition Match + Similarity + Sentiment + Rating)
              </span>
            </div>

            {recommendedList.length === 0 ? (
              <div className="p-8 bg-slate-50 border border-slate-200 rounded-xl text-center space-y-2">
                <FilterX className="w-8 h-8 text-slate-400 mx-auto" />
                <h4 className="text-sm font-semibold text-slate-700">
                  No matching recommendations were returned for this profile.
                </h4>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  {filteredList.length > 0
                    ? `${filteredList.length} candidate(s) were identified for ${patientSummary?.condition}, but all were excluded according to safety screening rules (see filtered conflicts below).`
                    : `No cataloged medications were found mapped to "${patientSummary?.condition}" in the review database.`}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {recommendedList.map((drug, index) => (
                  <RecommendationCard key={drug.drug_id} drug={drug} rank={index + 1} />
                ))}
              </div>
            )}
          </div>

          {/* 2. FILTERED UNSAFE CANDIDATES SECTION */}
          {filteredList.length > 0 && (
            <div className="space-y-4 pt-4 border-t border-slate-200">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold uppercase tracking-wider text-rose-800 flex items-center gap-2">
                  <AlertOctagon className="w-4 h-4 text-rose-600" />
                  <span>
                    Filtered Unsafe Candidates ({filteredList.length})
                  </span>
                </h3>
                <span className="text-xs text-rose-700 font-medium">
                  Excluded Exclusively by Deterministic Safety Knowledge Base
                </span>
              </div>

              <div className="space-y-4">
                {filteredList.map((drug) => (
                  <FilteredDrugCard key={drug.drug_id} drug={drug} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* IDLE STATE */}
      {requestState === STATES.IDLE && (
        <div className="bg-slate-50 border border-slate-200 border-dashed rounded-xl p-8 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center mx-auto text-slate-500">
            <HelpCircle className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-800">
              Ready for Decision Support Analysis
            </h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 leading-relaxed">
              Enter the patient's condition, age, optional symptoms, known allergies, and active medications above. Click <strong>"Analyze Profile"</strong> to evaluate candidates through multi-factor recommendation scoring and independent safety constraint screening.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
