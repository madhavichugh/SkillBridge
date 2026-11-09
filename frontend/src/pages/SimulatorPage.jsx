import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  ArrowRight, 
  CheckSquare, 
  Square, 
  Sparkles, 
  Layers, 
  Info, 
  RotateCcw,
  CheckCircle2,
  SlidersHorizontal
} from 'lucide-react';
import { simulateSkillUplift } from '../api';
import CategoryBreakdown from '../components/CategoryBreakdown';

export default function SimulatorPage({ data, onNavigate, onSkillsSelectedForRoadmap }) {
  if (!data) {
    return (
      <div className="text-center p-12 bg-white rounded-2xl border border-slate-200">
        <p className="text-sm text-slate-500">No analysis data available. Please upload a resume first.</p>
      </div>
    );
  }

  const { overall_score, company_name, company_type, skill_matches, category_breakdowns } = data;

  // Filter missing or underrepresented skills
  const availableGaps = skill_matches
    .filter((m) => m.status === 'Missing' || m.status === 'Underrepresented')
    .sort((a, b) => (a.importance_rank || 99) - (b.importance_rank || 99));

  const [selectedSkills, setSelectedSkills] = useState([]);
  const [simResult, setSimResult] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // Trigger simulation when selectedSkills change
  useEffect(() => {
    let isCancelled = false;

    const runSimulation = async () => {
      setIsSimulating(true);
      try {
        const payload = {
          company_type,
          current_overall_score: overall_score,
          acquired_skills: selectedSkills,
          all_skill_matches: skill_matches,
        };
        const result = await simulateSkillUplift(payload);
        if (!isCancelled) {
          setSimResult(result);
        }
      } catch (err) {
        console.error("Simulation failed:", err);
      } finally {
        if (!isCancelled) {
          setIsSimulating(false);
        }
      }
    };

    runSimulation();

    return () => {
      isCancelled = true;
    };
  }, [selectedSkills, overall_score, company_type, skill_matches]);

  const toggleSkill = (skillName) => {
    setSelectedSkills((prev) => 
      prev.includes(skillName) 
        ? prev.filter((s) => s !== skillName)
        : [...prev, skillName]
    );
  };

  const handleSelectTop3 = () => {
    const top3 = availableGaps.slice(0, 3).map((g) => g.skill);
    setSelectedSkills(top3);
  };

  const handleSelectAll = () => {
    const all = availableGaps.map((g) => g.skill);
    setSelectedSkills(all);
  };

  const handleReset = () => {
    setSelectedSkills([]);
  };

  const simulatedScore = simResult ? simResult.simulated_score : overall_score;
  const uplift = simResult ? simResult.uplift : 0.0;
  const displayBreakdowns = (simResult && simResult.updated_breakdowns) ? simResult.updated_breakdowns : category_breakdowns;

  return (
    <div className="space-y-8">
      {/* 1. Comparison & Uplift Hero Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
          <div className="flex-1 text-center lg:text-left">
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100 mb-3">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Predictive Uplift Simulator</span>
            </div>

            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              Test How Acquiring Skills Boosts Your Alignment
            </h2>
            <p className="text-sm text-slate-500 mt-1 max-w-xl">
              Toggle the missing requirements below. SkillBridge uses the exact mathematical scoring function and <span className="font-semibold text-slate-700">{company_name}</span> weights to compute your real-time uplift.
            </p>
          </div>

          {/* Before vs. After Score Meter */}
          <div className="flex items-center space-x-4 bg-slate-50 border border-slate-200/80 rounded-2xl p-4 sm:p-6 flex-shrink-0">
            {/* Baseline Score */}
            <div className="text-center px-2">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Current
              </p>
              <p className="text-3xl font-extrabold text-slate-600">
                {Math.round(overall_score)}%
              </p>
            </div>

            <div className="text-slate-300 font-bold text-lg">→</div>

            {/* Simulated Score */}
            <div className="text-center px-2">
              <p className="text-[11px] font-semibold text-indigo-600 uppercase tracking-wider">
                Simulated
              </p>
              <p className="text-3xl font-extrabold text-indigo-600">
                {Math.round(simulatedScore)}%
              </p>
            </div>

            {/* Uplift Pill */}
            <div className="ml-2 pl-4 border-l border-slate-200 flex flex-col items-center">
              <span className={`px-3 py-1.5 rounded-xl text-sm font-extrabold ${
                uplift > 0 
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200 shadow-xs' 
                  : 'bg-slate-200 text-slate-600'
              }`}>
                +{uplift}%
              </span>
              <span className="text-[10px] text-slate-400 mt-1">Net Uplift</span>
            </div>
          </div>
        </div>

        {/* Explainable Text Alert */}
        {simResult && simResult.explanation && (
          <div className="mt-6 p-4 rounded-xl bg-indigo-50/60 border border-indigo-100 text-xs text-indigo-900 flex items-start space-x-2.5">
            <Info className="w-4 h-4 text-indigo-600 flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <span className="font-bold">Score Mechanics: </span>
              {simResult.explanation}
            </p>
          </div>
        )}
      </div>

      {/* 2. Interactive Toggles & Category Breakdown Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Interactive Skill Toggles */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                <SlidersHorizontal className="w-4 h-4 text-indigo-600" />
                <span>Select Skills You Will Learn ({selectedSkills.length} selected)</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Check any skill to simulate full competency (1.0 credit) in the scoring model.
              </p>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center space-x-2">
              <button
                onClick={handleSelectTop3}
                className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors border border-indigo-100"
              >
                Top 3 Gaps
              </button>
              <button
                onClick={handleSelectAll}
                className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
              >
                Select All
              </button>
              {selectedSkills.length > 0 && (
                <button
                  onClick={handleReset}
                  className="text-xs text-slate-400 hover:text-rose-600 flex items-center space-x-1 px-1.5 py-1 transition-colors"
                  title="Clear selection"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Reset</span>
                </button>
              )}
            </div>
          </div>

          {availableGaps.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-xs">
              All listed skills already match strongly with your profile!
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {availableGaps.map((item, idx) => {
                const isSelected = selectedSkills.includes(item.skill);
                const isMissing = item.status === 'Missing';

                return (
                  <div
                    key={idx}
                    onClick={() => toggleSkill(item.skill)}
                    className={`cursor-pointer rounded-xl p-3.5 border transition-all flex items-start space-x-3 ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50/50 ring-2 ring-indigo-500/10'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="mt-0.5 text-indigo-600 flex-shrink-0">
                      {isSelected ? (
                        <CheckSquare className="w-4 h-4 text-indigo-600" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-300" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-900 truncate">
                          {item.skill}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          #{item.importance_rank || idx + 1}
                        </span>
                      </div>

                      <div className="flex items-center space-x-2 mt-1.5">
                        <span className="capitalize text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                          {item.category.replace('_', ' ')}
                        </span>
                        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                          isMissing ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-700'
                        }`}>
                          {item.status}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Action CTA to Roadmap */}
          {selectedSkills.length > 0 && (
            <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
              <span className="text-xs text-slate-500">
                Ready to bridge these gaps? Generate an effort-vs-impact learning sequence.
              </span>
              <button
                onClick={() => {
                  if (onSkillsSelectedForRoadmap) {
                    onSkillsSelectedForRoadmap(selectedSkills);
                  }
                  onNavigate('roadmap');
                }}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-100 transition-all self-stretch sm:self-auto justify-center"
              >
                <Sparkles className="w-4 h-4" />
                <span>Build Learning Roadmap ({selectedSkills.length})</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </button>
            </div>
          )}
        </div>

        {/* Right 1 Col: Dynamically Updated Category Breakdown */}
        <div className="space-y-4">
          <CategoryBreakdown breakdowns={displayBreakdowns} />
        </div>
      </div>
    </div>
  );
}
