import React from 'react';
import { Award, Briefcase, Info, Sparkles } from 'lucide-react';

export default function ScoreCard({ score, companyName, companyType, inferredRole }) {
  // Determine rating tier
  let ratingLabel = "Needs Alignment";
  let ratingColor = "text-rose-600 bg-rose-50 border-rose-200";
  let ringColor = "stroke-rose-500";
  let message = "Significant gaps in high-weighted skills. Follow the learning roadmap below to close them.";

  if (score >= 80) {
    ratingLabel = "Strong Fit";
    ratingColor = "text-emerald-700 bg-emerald-50 border-emerald-200";
    ringColor = "stroke-emerald-500";
    message = "Your profile matches the core JD requirements well. Refine project metrics to stand out.";
  } else if (score >= 60) {
    ratingLabel = "Moderate Match";
    ratingColor = "text-amber-700 bg-amber-50 border-amber-200";
    ringColor = "stroke-amber-500";
    message = "Good foundational match, but critical tools or domain skills need strengthening.";
  }

  // SVG circular progress calculation
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 flex flex-col md:flex-row items-center justify-between gap-6">
      {/* Left: Qualitative Context */}
      <div className="flex-1 text-center md:text-left">
        <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 mb-3">
          <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${ratingColor}`}>
            {ratingLabel}
          </span>
          {inferredRole && (
            <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
              <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
              <span>Target Role: {inferredRole.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
            </span>
          )}
        </div>

        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
          Candidate Alignment Score
        </h2>
        <p className="text-sm text-slate-500 mt-1 max-w-lg">
          {message}
        </p>

        <div className="mt-4 flex items-center space-x-2 text-xs text-slate-400">
          <Info className="w-4 h-4 flex-shrink-0" />
          <span>Calculated via semantic requirement matching and qualifications analysis.</span>
        </div>
      </div>

      {/* Right: Circular Gauge */}
      <div className="relative flex items-center justify-center flex-shrink-0">
        <svg className="w-36 h-36 transform -rotate-90" viewBox="0 0 128 128">
          <circle
            cx="64"
            cy="64"
            r={radius}
            className="stroke-slate-100"
            strokeWidth="10"
            fill="transparent"
          />
          <circle
            cx="64"
            cy="64"
            r={radius}
            className={`${ringColor} transition-all duration-1000 ease-out`}
            strokeWidth="10"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
          />
        </svg>

        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className="text-4xl font-extrabold text-slate-900 tracking-tight">
            {Math.round(score)}
          </span>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            out of 100
          </span>
        </div>
      </div>
    </div>
  );
}
