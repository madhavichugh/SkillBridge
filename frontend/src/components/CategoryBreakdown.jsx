import React from 'react';
import { Layers, Wrench, Globe, Users, GraduationCap } from 'lucide-react';

const CATEGORY_ICONS = {
  hard_skills: Layers,
  tools_and_tech: Wrench,
  domain_knowledge: Globe,
  soft_skills: Users,
  education_and_exp: GraduationCap,
};

export default function CategoryBreakdown({ breakdowns = [] }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
      <h3 className="text-lg font-bold text-slate-900 mb-1 flex items-center space-x-2">
        <span>Category Alignment Breakdown</span>
      </h3>
      <p className="text-xs text-slate-500 mb-6">
        Each category is scored based on semantic matches and weighted according to your chosen company profile.
      </p>

      <div className="space-y-5">
        {breakdowns.map((cat) => {
          const Icon = CATEGORY_ICONS[cat.category_name] || Layers;
          const weightPct = Math.round(cat.weight * 100);
          const rawScore = Math.round(cat.raw_score);

          let barColor = "bg-rose-500";
          if (rawScore >= 75) barColor = "bg-emerald-500";
          else if (rawScore >= 50) barColor = "bg-amber-500";

          return (
            <div key={cat.category_name} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2 font-medium text-slate-800">
                  <div className="p-1 rounded-md bg-slate-100 text-slate-600">
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span>{cat.display_name}</span>
                  <span className="text-slate-400 font-normal">
                    ({cat.matched_items}/{cat.total_items} items matched)
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-[11px] font-semibold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                    Weight: {weightPct}%
                  </span>
                  <span className="font-bold text-slate-900 w-10 text-right">
                    {rawScore}%
                  </span>
                </div>
              </div>

              {/* Progress bar track */}
              <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full ${barColor} rounded-full transition-all duration-700 ease-out`}
                  style={{ width: `${Math.min(100, Math.max(0, rawScore))}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
