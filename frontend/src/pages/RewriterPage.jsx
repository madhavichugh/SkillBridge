import React, { useState, useEffect } from 'react';
import { 
  FileEdit, 
  Sparkles, 
  CheckCircle2, 
  Copy, 
  ArrowRight, 
  Sliders, 
  Lightbulb, 
  Check, 
  Layers,
  HelpCircle
} from 'lucide-react';
import { rewriteProjectExperience } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';

export default function RewriterPage({ data, onNavigate }) {
  const [resumeBullets, setResumeBullets] = useState([]);
  const [selectedBullet, setSelectedBullet] = useState('');
  const [customBullet, setCustomBullet] = useState('');
  const [targetSkills, setTargetSkills] = useState([]);
  const [isRewriting, setIsRewriting] = useState(false);
  const [rewriteResult, setRewriteResult] = useState(null);
  const [placeholderValues, setPlaceholderValues] = useState({});
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (data && data.resume_entities && data.resume_entities.projects_or_experiences) {
      const bullets = data.resume_entities.projects_or_experiences.filter((b) => b && b.length > 20);
      setResumeBullets(bullets);
      if (bullets.length > 0) {
        setSelectedBullet(bullets[0]);
      }
    }

    if (data && data.jd_entities && data.jd_entities.hard_skills) {
      setTargetSkills(data.jd_entities.hard_skills.slice(0, 4));
    }
  }, [data]);

  const activeInputText = customBullet.trim() ? customBullet : selectedBullet;

  const handleRewrite = async () => {
    if (!activeInputText.trim()) return;

    setIsRewriting(true);
    setCopied(false);
    try {
      const roleContext = data?.inferred_role || "Engineering Specialist";
      const res = await rewriteProjectExperience(
        activeInputText,
        roleContext,
        data ? data.company_type : "mid_size_product",
        targetSkills
      );
      setRewriteResult(res);

      // Initialize placeholder inputs
      const initialPlaceholders = {};
      (res.metrics_to_fill || []).forEach((placeholder) => {
        initialPlaceholders[placeholder] = '';
      });
      setPlaceholderValues(initialPlaceholders);
    } catch (err) {
      console.error("Failed to rewrite bullet:", err);
    } finally {
      setIsRewriting(false);
    }
  };

  // Compute final bullet with user-filled metrics
  const getRenderedBullet = () => {
    if (!rewriteResult) return '';
    let text = rewriteResult.rewritten_text;
    Object.entries(placeholderValues).forEach(([placeholder, val]) => {
      if (val.trim()) {
        text = text.replaceAll(placeholder, val.trim());
      }
    });
    return text;
  };

  const handleCopy = () => {
    const finalBullet = getRenderedBullet();
    navigator.clipboard.writeText(`• ${finalBullet}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="space-y-8">
      {/* 1. Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100 mb-2">
              <FileEdit className="w-3.5 h-3.5" />
              <span>Targeted Experience Re-Framing</span>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              Quantified Project Bullet Rewriter
            </h2>
            <p className="text-sm text-slate-500 mt-1 max-w-2xl">
              Turn passive responsibilities into high-impact Google XYZ statements (<span className="italic">"Accomplished [X] as measured by [Y], by doing [Z]"</span>). Never fabricates unverified metrics.
            </p>
          </div>
        </div>
      </div>

      {/* 2. Experience Selection & Input */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Choose or Enter Bullet */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
          <h3 className="text-base font-bold text-slate-900">
            1. Select or Enter Resume Experience
          </h3>

          {resumeBullets.length > 0 && (
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-700">
                Extracted from your resume:
              </label>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {resumeBullets.map((bullet, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      setSelectedBullet(bullet);
                      setCustomBullet('');
                    }}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                      selectedBullet === bullet && !customBullet.trim()
                        ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-medium'
                        : 'border-slate-200 hover:border-slate-300 text-slate-600'
                    }`}
                  >
                    • {bullet}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-2">
            <label className="block text-xs font-bold text-slate-700">
              Or paste/edit a custom bullet point:
            </label>
            <textarea
              rows={4}
              value={customBullet}
              onChange={(e) => setCustomBullet(e.target.value)}
              placeholder="e.g., Developed API endpoints and worked on PostgreSQL database performance..."
              className="w-full text-xs font-mono p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800 placeholder-slate-400"
            />
          </div>

          <button
            onClick={handleRewrite}
            disabled={isRewriting || !activeInputText.trim()}
            className="w-full inline-flex items-center justify-center space-x-2 py-3 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 text-white font-bold text-sm shadow-md shadow-indigo-100 transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span>{isRewriting ? "Re-framing Experience..." : "Re-frame with Quantified Impact"}</span>
          </button>
        </div>

        {/* Right: Output & Placeholder Customizer */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 mb-4">
              2. ATS-Optimized Output
            </h3>

            {isRewriting ? (
              <div className="py-12">
                <LoadingSpinner message="Re-framing bullet with strong industry action verbs..." />
              </div>
            ) : !rewriteResult ? (
              <div className="text-center py-12 text-slate-400 text-xs">
                Select an experience bullet on the left and click "Re-frame" to generate an optimized version.
              </div>
            ) : (
              <div className="space-y-6">
                {/* Action Verbs Used */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-semibold text-slate-400">Action Verbs:</span>
                  {rewriteResult.action_verbs_used.map((verb, idx) => (
                    <span 
                      key={idx}
                      className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100 text-[11px] font-bold"
                    >
                      {verb}
                    </span>
                  ))}
                </div>

                {/* Final Rendered Bullet */}
                <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/30">
                  <p className="text-xs text-slate-900 leading-relaxed font-medium">
                    • {getRenderedBullet()}
                  </p>
                </div>

                {/* Interactive Metric Customizer */}
                {rewriteResult.metrics_to_fill && rewriteResult.metrics_to_fill.length > 0 && (
                  <div className="space-y-3 bg-slate-50 border border-slate-100 rounded-xl p-4">
                    <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-800">
                      <Sliders className="w-3.5 h-3.5 text-indigo-600" />
                      <span>Fill In Your Real Numbers (No Fake Metrics):</span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {rewriteResult.metrics_to_fill.map((placeholder) => (
                        <div key={placeholder} className="space-y-1">
                          <label className="block text-[11px] font-mono text-slate-500 font-semibold">
                            {placeholder}:
                          </label>
                          <input
                            type="text"
                            value={placeholderValues[placeholder] || ''}
                            onChange={(e) => setPlaceholderValues({
                              ...placeholderValues,
                              [placeholder]: e.target.value
                            })}
                            placeholder="e.g. 24% or 150ms"
                            className="w-full text-xs p-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Strategy Explanation */}
                <div className="flex items-start space-x-2 text-xs text-slate-500">
                  <Lightbulb className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                  <p>{rewriteResult.explanation}</p>
                </div>
              </div>
            )}
          </div>

          {/* Copy Button */}
          {rewriteResult && (
            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <button
                onClick={handleCopy}
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-100 transition-all"
              >
                {copied ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-white" />
                    <span>Copied Bullet!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Copy Final Resume Bullet</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
