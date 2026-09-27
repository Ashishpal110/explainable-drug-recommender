import React, { useState } from 'react';
import { User, Activity, AlertCircle, Pill, Sliders, Play, X, Plus, AlertTriangle } from 'lucide-react';

/**
 * Patient Profile Input Form for Clinical Decision Support.
 * Collects age, primary condition, symptoms, allergies, and active medications.
 * Strictly excludes gender per project specifications.
 */
export default function PatientProfileForm({
  onSubmit,
  loading = false,
  availableConditions = [],
  availableAllergies = [],
}) {
  const [age, setAge] = useState(52);
  const [condition, setCondition] = useState('High Blood Pressure');
  const [symptomInput, setSymptomInput] = useState('');
  const [symptoms, setSymptoms] = useState(['headache', 'fatigue']);
  const [allergyInput, setAllergyInput] = useState('');
  const [allergies, setAllergies] = useState(['ACE Inhibitors']);
  const [medicationInput, setMedicationInput] = useState('');
  const [currentMedications, setCurrentMedications] = useState(['Potassium Chloride']);

  const [validationErrors, setValidationErrors] = useState({});

  const [showWeights, setShowWeights] = useState(false);
  const [weights, setWeights] = useState({
    condition_match: 0.40,
    similarity: 0.30,
    sentiment: 0.20,
    rating: 0.10,
  });

  const handleAddSymptom = () => {
    const val = symptomInput.trim();
    if (val && !symptoms.includes(val)) {
      setSymptoms([...symptoms, val]);
      setSymptomInput('');
    }
  };

  const handleRemoveSymptom = (s) => {
    setSymptoms(symptoms.filter((item) => item !== s));
  };

  const handleAddAllergy = (allergyToAdd) => {
    const val = (allergyToAdd || allergyInput).trim();
    if (val && !allergies.includes(val)) {
      setAllergies([...allergies, val]);
      setAllergyInput('');
    }
  };

  const handleRemoveAllergy = (a) => {
    setAllergies(allergies.filter((item) => item !== a));
  };

  const handleAddMedication = () => {
    const val = medicationInput.trim();
    if (val && !currentMedications.includes(val)) {
      setCurrentMedications([...currentMedications, val]);
      setMedicationInput('');
    }
  };

  const handleRemoveMedication = (m) => {
    setCurrentMedications(currentMedications.filter((item) => item !== m));
  };

  const validate = () => {
    const errors = {};
    const numAge = Number(age);

    if (age === '' || isNaN(numAge)) {
      errors.age = 'Patient age is required.';
    } else if (numAge < 0 || numAge > 125) {
      errors.age = 'Patient age must be between 0 and 125 years.';
    }

    if (!condition || !condition.trim()) {
      errors.condition = 'Primary medical condition is required.';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) {
      return;
    }

    onSubmit({
      age: Number(age),
      condition: condition.trim(),
      symptoms: symptoms || [],
      allergies: allergies || [],
      current_medications: currentMedications || [],
      weights: showWeights ? weights : undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
      <div className="border-b border-slate-100 pb-4">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-600" />
          <span>Patient Profile & Safety Audit Intake</span>
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Specify clinical condition and patient safety parameters. The backend screening engine independently audits candidates against deterministic safety rules.
        </p>
      </div>

      {/* General Validation Error Alert */}
      {Object.keys(validationErrors).length > 0 && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-900 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-rose-950">Please correct the profile input errors:</div>
            <ul className="list-disc pl-4 mt-1 space-y-0.5">
              {Object.values(validationErrors).map((msg, i) => (
                <li key={i}>{msg}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Patient Age */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center gap-1.5">
            <User className="w-3.5 h-3.5 text-slate-500" />
            <span>Patient Age (Years) *</span>
          </label>
          <input
            type="number"
            min="0"
            max="125"
            required
            value={age}
            onChange={(e) => {
              setAge(e.target.value);
              if (validationErrors.age) {
                setValidationErrors({ ...validationErrors, age: null });
              }
            }}
            className={`w-full px-3.5 py-2 border rounded-lg text-sm outline-none transition-colors ${
              validationErrors.age
                ? 'border-rose-300 focus:ring-2 focus:ring-rose-500 bg-rose-50/30'
                : 'border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
            }`}
            placeholder="e.g. 52"
          />
          {validationErrors.age && (
            <p className="text-[11px] text-rose-600 mt-1 font-medium">{validationErrors.age}</p>
          )}
        </div>

        {/* Primary Condition */}
        <div className="md:col-span-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-slate-500" />
            <span>Primary Condition / Indication *</span>
          </label>
          <div className="relative">
            <input
              type="text"
              required
              value={condition}
              onChange={(e) => {
                setCondition(e.target.value);
                if (validationErrors.condition) {
                  setValidationErrors({ ...validationErrors, condition: null });
                }
              }}
              list="conditions-datalist"
              className={`w-full px-3.5 py-2 border rounded-lg text-sm outline-none transition-colors ${
                validationErrors.condition
                  ? 'border-rose-300 focus:ring-2 focus:ring-rose-500 bg-rose-50/30'
                  : 'border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
              }`}
              placeholder="e.g. High Blood Pressure, Depression, Type 2 Diabetes..."
            />
            {availableConditions.length > 0 && (
              <datalist id="conditions-datalist">
                {availableConditions.map((c) => (
                  <option key={c.condition_id} value={c.name} />
                ))}
              </datalist>
            )}
          </div>
          {validationErrors.condition && (
            <p className="text-[11px] text-rose-600 mt-1 font-medium">{validationErrors.condition}</p>
          )}
        </div>
      </div>

      {/* Reported Symptoms */}
      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
          Reported Symptoms (Optional for Content Similarity)
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={symptomInput}
            onChange={(e) => setSymptomInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddSymptom();
              }
            }}
            placeholder="Type symptom (e.g. dizziness, fatigue) & press Enter"
            className="flex-1 px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
          />
          <button
            type="button"
            onClick={handleAddSymptom}
            className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add</span>
          </button>
        </div>
        {symptoms.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {symptoms.map((s) => (
              <span
                key={s}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-800 border border-slate-200"
              >
                <span>{s}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveSymptom(s)}
                  className="hover:text-rose-600 focus:outline-none"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Known Allergies & Active Current Medications */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2 border-t border-slate-100">
        {/* Allergies */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-rose-800 mb-1.5 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>Known Allergies / Allergen Classes</span>
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={allergyInput}
              onChange={(e) => setAllergyInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddAllergy();
                }
              }}
              list="allergies-datalist"
              placeholder="e.g. ACE Inhibitors, Penicillins, NSAIDs"
              className="flex-1 px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-rose-500 focus:border-rose-500 outline-none"
            />
            {availableAllergies.length > 0 && (
              <datalist id="allergies-datalist">
                {availableAllergies.map((a) => (
                  <option key={a} value={a} />
                ))}
              </datalist>
            )}
            <button
              type="button"
              onClick={() => handleAddAllergy()}
              className="px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-xs font-semibold flex items-center gap-1 border border-rose-200 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          </div>
          {allergies.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {allergies.map((a) => (
                <span
                  key={a}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200"
                >
                  <span>{a}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveAllergy(a)}
                    className="hover:text-rose-950 focus:outline-none"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Current Medications */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5 flex items-center gap-1.5">
            <Pill className="w-3.5 h-3.5 text-indigo-600" />
            <span>Active Current Medications (for DDI Screening)</span>
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={medicationInput}
              onChange={(e) => setMedicationInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddMedication();
                }
              }}
              placeholder="e.g. Potassium Chloride, Warfarin, Metformin"
              className="flex-1 px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            />
            <button
              type="button"
              onClick={handleAddMedication}
              className="px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-semibold flex items-center gap-1 border border-indigo-200 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          </div>
          {currentMedications.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {currentMedications.map((m) => (
                <span
                  key={m}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-indigo-50 text-indigo-800 border border-indigo-200"
                >
                  <span>{m}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveMedication(m)}
                    className="hover:text-indigo-950 focus:outline-none"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Advanced Heuristic Weight Sliders (Collapsible) */}
      <div className="pt-2 border-t border-slate-100">
        <button
          type="button"
          onClick={() => setShowWeights(!showWeights)}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-indigo-600 focus:outline-none"
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>{showWeights ? 'Hide Custom Weights' : 'Configure Custom Recommendation Weights (Advanced)'}</span>
        </button>

        {showWeights && (
          <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-3">
            <p className="text-xs text-slate-500">
              Heuristic weights for recommendation factors (weights are normalized to sum to 1.0). Deterministic safety screening operates independently.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                  <span>Condition Match</span>
                  <span>{weights.condition_match}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={weights.condition_match}
                  onChange={(e) => setWeights({ ...weights, condition_match: parseFloat(e.target.value) })}
                  className="w-full accent-indigo-600"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                  <span>Profile Similarity</span>
                  <span>{weights.similarity}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={weights.similarity}
                  onChange={(e) => setWeights({ ...weights, similarity: parseFloat(e.target.value) })}
                  className="w-full accent-indigo-600"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                  <span>Review Sentiment</span>
                  <span>{weights.sentiment}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={weights.sentiment}
                  onChange={(e) => setWeights({ ...weights, sentiment: parseFloat(e.target.value) })}
                  className="w-full accent-indigo-600"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
                  <span>Historical Rating</span>
                  <span>{weights.rating}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={weights.rating}
                  onChange={(e) => setWeights({ ...weights, rating: parseFloat(e.target.value) })}
                  className="w-full accent-indigo-600"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Submit Action */}
      <div className="flex justify-end pt-2">
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white font-semibold text-sm rounded-lg shadow-sm transition-colors focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 outline-none"
        >
          <Play className="w-4 h-4 fill-white" />
          <span>{loading ? 'Screening & Scoring Candidates...' : 'Analyze Profile'}</span>
        </button>
      </div>
    </form>
  );
}
