import React, { useState, useEffect } from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  Briefcase, 
  Flame, 
  Info, 
  ArrowUpRight,
  Sparkles
} from 'lucide-react';
import { getSalaryInsights } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';

export default function SalaryGrowthPage({ data }) {
  // Use detected role from analysis session if available
  const detectedRole = data?.inferred_role || 'default';

  const [currency, setCurrency] = useState('USD');
  const [yearsExp, setYearsExp] = useState(3.0);
  const [salaryData, setSalaryData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize years of experience from resume entities if available
  useEffect(() => {
    if (data?.resume_entities?.years_of_experience) {
      setYearsExp(data.resume_entities.years_of_experience);
    }
  }, [data]);

  // Fetch salary insights for the detected role
  useEffect(() => {
    const fetchSalary = async () => {
      setIsLoading(true);
      try {
        const res = await getSalaryInsights(detectedRole, currency);
        setSalaryData(res);
      } catch (err) {
        console.error("Failed to fetch salary data:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSalary();
  }, [detectedRole, currency]);

  // Format currency helper
  const formatCurrency = (val, curr) => {
    if (!val) return '—';
    if (curr === 'USD') {
      return `$${Number(val).toLocaleString()}`;
    }
    // For INR, format with Lakhs (LPA) notation
    if (val >= 100000) {
      const lpa = (val / 100000).toFixed(1);
      return `₹${Number(val).toLocaleString()} (${lpa} LPA)`;
    }
    return `₹${Number(val).toLocaleString()}`;
  };

  return (
    <div className="space-y-8">
      {/* 1. Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                <DollarSign className="w-3.5 h-3.5" />
                <span>Market Compensation Intelligence</span>
              </div>
              {salaryData?.role_title && (
                <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Target Role: {salaryData.role_title}</span>
                </div>
              )}
            </div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              Salary Benchmarks & 5-Year Career Trajectory
            </h2>
            <p className="text-sm text-slate-500 mt-1 max-w-2xl">
              Competitive compensation intelligence and progression trajectory based on your target role, experience level, and high-impact specialized skills.
            </p>
          </div>

          {/* Currency Toggle */}
          <div className="flex items-center space-x-1 p-1 bg-slate-100 rounded-xl border border-slate-200 self-start md:self-auto">
            <button
              onClick={() => setCurrency('USD')}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                currency === 'USD'
                  ? 'bg-white text-indigo-700 shadow-xs'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              USD ($ Global)
            </button>
            <button
              onClick={() => setCurrency('INR')}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                currency === 'INR'
                  ? 'bg-white text-indigo-700 shadow-xs'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              INR (₹ India LPA)
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12">
          <LoadingSpinner message="Calculating compensation projections for your target role..." />
        </div>
      ) : salaryData ? (
        <div className="space-y-8">
          {/* Active Role Meta Banner */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 bg-indigo-50/60 rounded-xl border border-indigo-100 text-xs">
            <div className="flex items-center space-x-2">
              <Briefcase className="w-4 h-4 text-indigo-700" />
              <span className="font-bold text-slate-800">
                Active Benchmark: <span className="text-indigo-700 font-extrabold">{salaryData.role_title}</span>
              </span>
              <span className="px-2 py-0.5 rounded-md bg-white text-indigo-600 font-semibold border border-indigo-200">
                {salaryData.category || 'Professional Practice'}
              </span>
            </div>
            <span className="text-slate-500 mt-1 sm:mt-0">
              Market compensation estimates in {currency}
            </span>
          </div>

          {/* 2. Salary Range Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Min */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Indicative Minimum
              </span>
              <p className="text-2xl font-extrabold text-slate-700">
                {formatCurrency(salaryData.range.min, currency)}
              </p>
              <p className="text-[11px] text-slate-400">
                Baseline entry compensation for candidates meeting primary core qualifications.
              </p>
            </div>

            {/* Median (Highlighted) */}
            <div className="bg-gradient-to-br from-indigo-900 to-indigo-700 text-white rounded-2xl border border-indigo-600 shadow-md p-6 space-y-2 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-indigo-200 uppercase tracking-wider">
                  Median Market Benchmark
                </span>
                <span className="text-[10px] font-bold bg-white/20 text-white px-2 py-0.5 rounded-md">
                  Target
                </span>
              </div>
              <p className="text-3xl font-extrabold text-white">
                {formatCurrency(salaryData.range.median, currency)}
              </p>
              <p className="text-[11px] text-indigo-100">
                Market average for {salaryData.role_title} with proven execution and competency alignment.
              </p>
            </div>

            {/* Max */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Top-Tier Candidate Ceiling
              </span>
              <p className="text-2xl font-extrabold text-slate-900">
                {formatCurrency(salaryData.range.max, currency)}
              </p>
              <p className="text-[11px] text-slate-400">
                Commanded by top-performing candidates with high-impact specialized skills or credentials.
              </p>
            </div>
          </div>

          {/* 3. 5-Year Growth Projections & High-Impact Skills Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left 2 Cols: 5-Year Trajectory */}
            <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">
                  Career Growth Projection (Years 1 to 5)
                </h3>
              </div>
              <p className="text-xs text-slate-500">
                Projected compensation trajectory as you gain senior domain mastery, lead key initiatives, and close critical skill gaps.
              </p>

              <div className="space-y-4">
                {salaryData.growth_projection.map((item, idx) => {
                  const val = currency === 'USD' ? item.usd : item.inr;
                  const maxVal = currency === 'USD' 
                    ? salaryData.growth_projection[salaryData.growth_projection.length - 1].usd 
                    : salaryData.growth_projection[salaryData.growth_projection.length - 1].inr;
                  const widthPct = Math.min(100, Math.round((val / maxVal) * 100));

                  return (
                    <div key={idx} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-800">
                          {item.year}
                        </span>
                        <span className="font-bold text-indigo-700">
                          {formatCurrency(val, currency)}
                        </span>
                      </div>

                      <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-full transition-all duration-700 ease-out"
                          style={{ width: `${widthPct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right 1 Col: High-Impact Skill Premiums */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
              <div className="flex items-center space-x-2">
                <Flame className="w-5 h-5 text-amber-500" />
                <h3 className="text-base font-bold text-slate-900">
                  High-Impact Skill Premiums
                </h3>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Adding these specific competencies or credentials to your portfolio commands direct compensation premiums in hiring negotiations:
              </p>

              <div className="space-y-3 pt-2">
                {salaryData.high_impact_skills.map((skillItem, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl border border-slate-100 bg-slate-50 flex items-center justify-between"
                  >
                    <span className="text-xs font-semibold text-slate-800 truncate pr-2">
                      {skillItem.skill}
                    </span>
                    <span className="inline-flex items-center space-x-0.5 text-xs font-extrabold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md flex-shrink-0">
                      <ArrowUpRight className="w-3.5 h-3.5" />
                      <span>+{skillItem.premium_percent}%</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 4. Indicative Estimate Disclaimer */}
          <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-900 text-xs flex items-start space-x-3">
            <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Indicative Market Estimates: </span>
              {salaryData.disclaimer}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
