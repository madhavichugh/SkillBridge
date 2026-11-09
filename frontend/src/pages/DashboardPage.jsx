import React, { useState } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  ArrowRight, 
  TrendingUp,
  Layers,
  Sparkles
} from 'lucide-react';
import ScoreCard from '../components/ScoreCard';
import CategoryBreakdown from '../components/CategoryBreakdown';
import SkillTag from '../components/SkillTag';

export default function DashboardPage({ data, onNavigate }) {
  const [filter, setFilter] = useState('all'); // 'all', 'strong', 'partial', 'missing'

  if (!data) {
    return (
      <div className="text-center p-12 bg-white rounded-2xl border border-slate-200">
        <p className="text-sm text-slate-500">No analysis data available. Please upload a resume first.</p>
      </div>
    );
  }

  const { overall_score, company_name, company_type, category_breakdowns, skill_matches } = data;

  // Separate matches by status
  const strongMatches = skill_matches.filter((m) => m.status === 'Strong match');
  const partialMatches = skill_matches.filter((m) => m.status === 'Underrepresented');
  const missingMatches = skill_matches.filter((m) => m.status === 'Missing');

  // Filtered skills list
  const filteredSkills = skill_matches.filter((item) => {
    if (filter === 'strong') return item.status === 'Strong match';
    if (filter === 'partial') return item.status === 'Underrepresented';
    if (filter === 'missing') return item.status === 'Missing';
    return true;
  });

  return (
    <div className="space-y-8">
      {/* 1. Top Overall Alignment Score Banner */}
      <ScoreCard
        score={overall_score}
        companyName={company_name}
        companyType={company_type}
        inferredRole={data.inferred_role}
      />

      {/* 2. Middle Grid: Category Progress & Quick Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Category Progress Bars */}
        <div className="lg:col-span-2">
          <CategoryBreakdown breakdowns={category_breakdowns} />
        </div>

        {/* Right 1 Col: Match Breakdown Metrics & Fast Actions */}
        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">
              Requirements Breakdown
            </h3>

            <div className="space-y-3">
              <div 
                onClick={() => setFilter('strong')}
                className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all ${
                  filter === 'strong' ? 'border-emerald-500 bg-emerald-50/60' : 'border-slate-100 bg-slate-50 hover:bg-slate-100/70'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span className="text-xs font-semibold text-slate-800">Strong Matches</span>
                </div>
                <span className="text-sm font-extrabold text-emerald-700 bg-white px-2 py-0.5 rounded-md border border-emerald-100">
                  {strongMatches.length}
                </span>
              </div>

              <div 
                onClick={() => setFilter('partial')}
                className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all ${
                  filter === 'partial' ? 'border-amber-500 bg-amber-50/60' : 'border-slate-100 bg-slate-50 hover:bg-slate-100/70'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <span className="text-xs font-semibold text-slate-800">Underrepresented</span>
                </div>
                <span className="text-sm font-extrabold text-amber-700 bg-white px-2 py-0.5 rounded-md border border-amber-100">
                  {partialMatches.length}
                </span>
              </div>

              <div 
                onClick={() => setFilter('missing')}
                className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all ${
                  filter === 'missing' ? 'border-rose-500 bg-rose-50/60' : 'border-slate-100 bg-slate-50 hover:bg-slate-100/70'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <XCircle className="w-4 h-4 text-rose-600" />
                  <span className="text-xs font-semibold text-slate-800">Missing Requirements</span>
                </div>
                <span className="text-sm font-extrabold text-rose-700 bg-white px-2 py-0.5 rounded-md border border-rose-100">
                  {missingMatches.length}
                </span>
              </div>
            </div>

            {/* Quick Action to Simulator */}
            <div className="pt-2">
              <button
                onClick={() => onNavigate('simulator')}
                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold transition-colors border border-indigo-200/50"
              >
                <TrendingUp className="w-4 h-4" />
                <span>Simulate Score Uplift</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Detailed Skills Grid */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              <Layers className="w-5 h-5 text-indigo-600" />
              <span>Semantic Skill Matches & Gaps</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Every JD requirement evaluated with dense vector embeddings against your resume.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap gap-1.5 p-1 bg-slate-100 rounded-xl self-start sm:self-auto">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                filter === 'all' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All ({skill_matches.length})
            </button>
            <button
              onClick={() => setFilter('strong')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                filter === 'strong' ? 'bg-white text-emerald-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Strong ({strongMatches.length})
            </button>
            <button
              onClick={() => setFilter('partial')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                filter === 'partial' ? 'bg-white text-amber-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Partial ({partialMatches.length})
            </button>
            <button
              onClick={() => setFilter('missing')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                filter === 'missing' ? 'bg-white text-rose-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Missing ({missingMatches.length})
            </button>
          </div>
        </div>

        {filteredSkills.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs">
            No requirements match the selected filter.
          </div>
        ) : (
          <div className="flex flex-wrap gap-2.5">
            {filteredSkills.map((item, idx) => (
              <SkillTag
                key={`${item.skill}-${idx}`}
                skill={item.skill}
                status={item.status}
                similarityScore={item.similarity_score}
                matchedWith={item.matched_with}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
