import React from 'react';
import { 
  AlertTriangle, 
  UserX, 
  CheckCircle2, 
  ArrowRight, 
  Layers, 
  Lightbulb, 
  FileSearch, 
  Building2,
  TrendingUp,
  Sparkles
} from 'lucide-react';

export default function GapAnalysisPage({ data, onNavigate }) {
  if (!data) {
    return (
      <div className="text-center p-12 bg-white rounded-2xl border border-slate-200">
        <p className="text-sm text-slate-500">No analysis data available. Please upload a resume first.</p>
      </div>
    );
  }

  const { rejection_reasons, skill_matches, company_name, company_type } = data;

  // Filter missing and underrepresented gaps sorted by importance rank
  const rankedGaps = skill_matches
    .filter((m) => m.status === 'Missing' || m.status === 'Underrepresented')
    .sort((a, b) => (a.importance_rank || 99) - (b.importance_rank || 99));

  return (
    <div className="space-y-8">
      {/* 1. Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-rose-600 font-bold text-xs uppercase tracking-wider mb-1">
              <AlertTriangle className="w-4 h-4" />
              <span>Prioritized Skill Gaps & Rejection Risk</span>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              Recruiter-Style Screening Analysis
            </h2>
            <p className="text-sm text-slate-500 mt-1 max-w-2xl">
              Hiring managers spend an average of 7 seconds screening a resume. Here is how your qualifications read against the key target job requirements.
            </p>
          </div>

          <button
            onClick={() => onNavigate('simulator')}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-100 transition-all self-start md:self-auto"
          >
            <TrendingUp className="w-4 h-4" />
            <span>Test Score Uplift Simulator</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 2. Recruiter Perspective: Potential Rejection Reasons */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <UserX className="w-5 h-5 text-rose-600" />
            <h3 className="text-lg font-bold text-slate-900">
              Potential Rejection Reasons (Recruiter Perspective)
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-medium">
            Based on hiring team screening criteria
          </span>
        </div>

        {rejection_reasons.length === 0 ? (
          <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6 text-emerald-800 flex items-center space-x-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
            <div>
              <p className="text-sm font-bold">No high-risk rejection flags detected!</p>
              <p className="text-xs text-emerald-700 mt-0.5">Your resume covers the foundational requirements for this role.</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {rejection_reasons.map((rec, idx) => (
              <div 
                key={idx}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between hover:border-slate-300 transition-all"
              >
                <div>
                  {/* Badge & Title */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[11px] font-bold text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-full">
                      Hiring Risk #{idx + 1}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">
                      Linked: <span className="font-semibold text-slate-700">{rec.linked_gap}</span>
                    </span>
                  </div>

                  <h4 className="text-base font-bold text-slate-900 mb-2 leading-snug">
                    {rec.title}
                  </h4>

                  <p className="text-xs text-slate-600 leading-relaxed mb-4">
                    {rec.reason}
                  </p>

                  {/* Resume Evidence */}
                  <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 mb-4 space-y-1">
                    <div className="flex items-center space-x-1.5 text-[11px] font-bold text-slate-700">
                      <FileSearch className="w-3.5 h-3.5 text-slate-400" />
                      <span>Resume Evidence:</span>
                    </div>
                    <p className="text-xs text-slate-500 italic pl-5">
                      "{rec.resume_evidence}"
                    </p>
                  </div>
                </div>

                {/* Actionable Fix */}
                <div className="pt-3 border-t border-slate-100 flex items-start space-x-2">
                  <Lightbulb className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div className="text-xs">
                    <span className="font-bold text-slate-800">Actionable Fix: </span>
                    <span className="text-slate-600">{rec.actionable_fix}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3. Ranked Skill Gaps Priority Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex items-center space-x-2 mb-2">
          <Layers className="w-5 h-5 text-indigo-600" />
          <h3 className="text-lg font-bold text-slate-900">
            Ranked Skill Gaps (Impact vs. Effort)
          </h3>
        </div>
        <p className="text-xs text-slate-500 mb-6">
          Gaps are ranked by priority considering the JD emphasis, frequency of mentions, and weight assigned by {company_name}.
        </p>

        {rankedGaps.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-xs">
            No skill gaps found! Your profile aligns with all listed requirements.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="pb-3 px-3">Priority</th>
                  <th className="pb-3 px-3">Skill / Requirement</th>
                  <th className="pb-3 px-3">Category</th>
                  <th className="pb-3 px-3">Current Status</th>
                  <th className="pb-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {rankedGaps.map((gap, i) => {
                  const isMissing = gap.status === 'Missing';
                  return (
                    <tr key={i} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-3 font-mono font-bold text-indigo-600">
                        #{gap.importance_rank || i + 1}
                      </td>
                      <td className="py-3 px-3 font-bold text-slate-900">
                        {gap.skill}
                      </td>
                      <td className="py-3 px-3">
                        <span className="capitalize px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 font-medium">
                          {gap.category.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full font-semibold ${
                          isMissing
                            ? 'bg-rose-50 text-rose-700 border border-rose-200'
                            : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}>
                          {gap.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => onNavigate('simulator')}
                          className="inline-flex items-center space-x-1 text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors"
                        >
                          <span>Simulate</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
