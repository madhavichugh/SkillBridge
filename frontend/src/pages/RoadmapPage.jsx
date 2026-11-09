import React, { useState, useEffect } from 'react';
import { 
  Map, 
  Clock, 
  Sparkles, 
  CheckCircle2, 
  Copy, 
  ExternalLink, 
  Code2, 
  Flame, 
  Layers,
  ArrowRight
} from 'lucide-react';
import { getLearningRoadmap, generateResumeBullets } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';

export default function RoadmapPage({ data, initialSkills = [], onNavigate }) {
  const [missingSkills, setMissingSkills] = useState([]);
  const [roadmapSteps, setRoadmapSteps] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [bulletModalSkill, setBulletModalSkill] = useState(null);
  const [generatedBullets, setGeneratedBullets] = useState([]);
  const [isGeneratingBullet, setIsGeneratingBullet] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Initialize missing skills from analysis data or from simulator handoff
  useEffect(() => {
    let targetSkills = [];
    if (initialSkills && initialSkills.length > 0) {
      targetSkills = initialSkills;
    } else if (data && data.skill_matches) {
      targetSkills = data.skill_matches
        .filter((m) => m.status === 'Missing' || m.status === 'Underrepresented')
        .map((m) => m.skill);
    }

    setMissingSkills(targetSkills);

    const roleContext = data?.inferred_role || "Engineering Specialist";

    const fetchRoadmap = async () => {
      setIsLoading(true);
      try {
        const res = await getLearningRoadmap(targetSkills, roleContext);
        setRoadmapSteps(res.steps || []);
      } catch (err) {
        console.error("Failed to load roadmap:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRoadmap();
  }, [data, initialSkills]);

  // Handle generating bullets for a specific step
  const handleGenerateBullets = async (skill) => {
    setBulletModalSkill(skill);
    setIsGeneratingBullet(true);
    setCopiedIndex(null);
    try {
      const roleContext = data?.inferred_role || "Engineering Specialist";
      const res = await generateResumeBullets(skill, roleContext);
      setGeneratedBullets(res.bullet_options || []);
    } catch (err) {
      console.error("Failed to generate bullets:", err);
    } finally {
      setIsGeneratingBullet(false);
    }
  };

  const copyToClipboard = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2500);
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12">
        <LoadingSpinner message="Architecting Your Optimized Learning Roadmap..." />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 1. Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100 mb-2">
              <Map className="w-3.5 h-3.5" />
              <span>Step-by-Step Curriculum</span>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              Impact-Ranked Learning Roadmap
            </h2>
            <p className="text-sm text-slate-500 mt-1 max-w-2xl">
              Ordered by highest score impact vs. realistic learning effort. Develop these competencies, certifications, and deliverables to prove practical qualification to hiring teams.
            </p>
          </div>

          <button
            onClick={() => onNavigate('rewriter')}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-100 transition-all self-start md:self-auto"
          >
            <span>Project Rewriter Tool</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 2. Step-by-Step Sequence Cards */}
      <div className="space-y-4">
        {roadmapSteps.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-500 text-xs">
            No learning steps required! Your profile matches all listed JD requirements.
          </div>
        ) : (
          roadmapSteps.map((step) => {
            let effortBadge = "bg-emerald-50 text-emerald-800 border-emerald-200";
            if (step.effort_level === "High") {
              effortBadge = "bg-rose-50 text-rose-800 border-rose-200";
            } else if (step.effort_level === "Medium") {
              effortBadge = "bg-amber-50 text-amber-800 border-amber-200";
            }

            return (
              <div 
                key={step.step_number}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 transition-all hover:border-slate-300 flex flex-col md:flex-row gap-6 items-start"
              >
                {/* Step Number Circle */}
                <div className="w-12 h-12 rounded-2xl bg-indigo-600 text-white flex flex-col items-center justify-center font-bold flex-shrink-0 shadow-sm">
                  <span className="text-[10px] uppercase tracking-wider opacity-80 leading-none">Step</span>
                  <span className="text-lg leading-tight">#{step.step_number}</span>
                </div>

                {/* Main Content */}
                <div className="flex-1 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="text-lg font-bold text-slate-900">
                      {step.skill}
                    </h3>

                    {/* Metadata Badges */}
                    <div className="flex items-center space-x-2 text-xs">
                      <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100">
                        <Flame className="w-3.5 h-3.5 text-indigo-500" />
                        <span>+{step.impact_score}% Score Uplift</span>
                      </span>

                      <span className={`px-2.5 py-1 rounded-full font-semibold border ${effortBadge}`}>
                        {step.effort_level} Effort
                      </span>

                      <span className="flex items-center space-x-1 text-slate-400">
                        <Clock className="w-3.5 h-3.5" />
                        <span>~{step.estimated_weeks} weeks</span>
                      </span>
                    </div>
                  </div>

                  {/* Why it matters */}
                  <p className="text-xs text-slate-600 leading-relaxed">
                    <span className="font-semibold text-slate-800">Why Recruiters Care: </span>
                    {step.why_it_matters}
                  </p>

                  {/* Suggested Project */}
                  <div className="bg-slate-50 border border-slate-100 rounded-xl p-3.5 flex items-start space-x-2.5">
                    <Code2 className="w-4 h-4 text-indigo-600 flex-shrink-0 mt-0.5" />
                    <div className="text-xs">
                      <span className="font-bold text-slate-800">Suggested Hands-On Project: </span>
                      <span className="text-slate-600">{step.suggested_project}</span>
                    </div>
                  </div>

                  {/* Action: Generate Resume Bullet */}
                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={() => handleGenerateBullets(step.skill)}
                      className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold transition-colors border border-indigo-200/50"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Generate Resume Bullet for {step.skill}</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* 3. Generated Resume Bullets Modal */}
      {bulletModalSkill && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-2xl w-full p-6 sm:p-8 space-y-6 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">
                  ATS Bullet Options
                </span>
                <h3 className="text-lg font-bold text-slate-900 mt-0.5">
                  Resume Bullets for {bulletModalSkill}
                </h3>
              </div>
              <button
                onClick={() => setBulletModalSkill(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-semibold p-1"
              >
                ✕
              </button>
            </div>

            {isGeneratingBullet ? (
              <div className="py-8 text-center">
                <LoadingSpinner message={`Crafting ATS-friendly bullets for ${bulletModalSkill}...`} />
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-xs text-slate-500">
                  Select and copy a tailored bullet. Replace bracketed placeholders like <span className="font-mono font-bold text-indigo-700 bg-indigo-50 px-1 py-0.5 rounded">[X%]</span> with your real achievements.
                </p>

                {generatedBullets.map((bullet, idx) => (
                  <div 
                    key={idx}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors space-y-3"
                  >
                    <p className="text-xs text-slate-800 leading-relaxed font-sans">
                      • {bullet}
                    </p>

                    <div className="flex justify-end">
                      <button
                        onClick={() => copyToClipboard(`• ${bullet}`, idx)}
                        className="inline-flex items-center space-x-1 px-3 py-1 rounded-md text-xs font-semibold bg-white border border-slate-200 hover:border-indigo-300 text-slate-700 hover:text-indigo-600 transition-colors shadow-2xs"
                      >
                        {copiedIndex === idx ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span className="text-emerald-700">Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>Copy Bullet</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setBulletModalSkill(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
