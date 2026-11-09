import React from 'react';
import { CheckCircle2, AlertCircle, XCircle } from 'lucide-react';

export default function SkillTag({ skill, status, similarityScore, matchedWith }) {
  let badgeStyle = "bg-slate-100 text-slate-700 border-slate-200";
  let Icon = AlertCircle;
  let label = "Missing";

  if (status === "Strong match") {
    badgeStyle = "bg-emerald-50 text-emerald-800 border-emerald-200";
    Icon = CheckCircle2;
    label = "Strong Match";
  } else if (status === "Underrepresented") {
    badgeStyle = "bg-amber-50 text-amber-800 border-amber-200";
    Icon = AlertCircle;
    label = "Partial Match";
  } else {
    badgeStyle = "bg-rose-50 text-rose-800 border-rose-200";
    Icon = XCircle;
    label = "Missing";
  }

  const percentage = Math.round((similarityScore || 0) * 100);

  return (
    <div className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${badgeStyle}`}>
      <Icon className="w-3.5 h-3.5 flex-shrink-0" />
      <span className="font-semibold text-slate-900">{skill}</span>
      <span className="text-[10px] opacity-80 px-1.5 py-0.5 rounded-md bg-white/60 font-mono">
        {percentage}%
      </span>
      {matchedWith && status !== "Missing" && (
        <span className="text-[10px] text-slate-500 italic hidden sm:inline">
          (via {matchedWith})
        </span>
      )}
    </div>
  );
}
