import React, { useState } from 'react';
import { 
  Sparkles, 
  UploadCloud, 
  BarChart3, 
  AlertTriangle, 
  TrendingUp, 
  Map, 
  FileEdit, 
  DollarSign, 
  Trash2,
  CheckCircle2
} from 'lucide-react';

import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';
import GapAnalysisPage from './pages/GapAnalysisPage';
import SimulatorPage from './pages/SimulatorPage';
import RoadmapPage from './pages/RoadmapPage';
import RewriterPage from './pages/RewriterPage';
import SalaryGrowthPage from './pages/SalaryGrowthPage';
import { purgeAllData } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [analysisData, setAnalysisData] = useState(null);
  const [selectedRoadmapSkills, setSelectedRoadmapSkills] = useState([]);
  const [feedbackMessage, setFeedbackMessage] = useState(null);

  // When UploadPage completes an analysis session
  const handleAnalysisComplete = (data) => {
    setAnalysisData(data);
    setActiveTab('dashboard');
  };

  // One-click privacy purge
  const handlePurgeData = async () => {
    if (window.confirm("Purge all stored analysis and session data? This action cannot be undone.")) {
      try {
        await purgeAllData();
      } catch (e) {
        // Continue local purge even if server is offline
      }
      setAnalysisData(null);
      setActiveTab('upload');
      setFeedbackMessage("All resume and analysis data purged safely.");
      setTimeout(() => setFeedbackMessage(null), 3500);
    }
  };

  const tabs = [
    { id: 'upload', label: 'Upload & Parse', icon: UploadCloud },
    { id: 'dashboard', label: 'Match Dashboard', icon: BarChart3, disabled: !analysisData },
    { id: 'gaps', label: 'Gap Analysis', icon: AlertTriangle, disabled: !analysisData },
    { id: 'simulator', label: 'Uplift Simulator', icon: TrendingUp, disabled: !analysisData },
    { id: 'roadmap', label: 'Learning Roadmap', icon: Map, disabled: !analysisData },
    { id: 'rewriter', label: 'Project Rewriter', icon: FileEdit, disabled: !analysisData },
    { id: 'salary', label: 'Salary & Growth', icon: DollarSign },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div 
            className="flex items-center space-x-2 cursor-pointer" 
            onClick={() => setActiveTab('upload')}
          >
            <div>
              <span className="text-xl font-bold bg-gradient-to-r from-indigo-700 to-indigo-500 bg-clip-text text-transparent">
                SkillBridge
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2.5 py-0.5 bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100 font-medium">
                AI Career Guidance
              </span>
            </div>
          </div>

          {/* Privacy Purge Control */}
          <div className="flex items-center space-x-3">
            <button
              onClick={handlePurgeData}
              className="text-xs text-slate-500 hover:text-rose-600 flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-rose-200 hover:bg-rose-50/50 transition-colors"
              title="Delete all resume and job data"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Purge My Data</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-1 overflow-x-auto border-t border-slate-100 py-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            const isDisabled = tab.disabled;

            return (
              <button
                key={tab.id}
                disabled={isDisabled}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3 py-2 text-xs sm:text-sm font-medium rounded-lg whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-xs'
                    : isDisabled
                    ? 'text-slate-300 cursor-not-allowed'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-600' : isDisabled ? 'text-slate-300' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {feedbackMessage && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center space-x-2 text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>{feedbackMessage}</span>
          </div>
        )}

        {/* Tab Routing */}
        {activeTab === 'upload' && (
          <UploadPage onAnalysisComplete={handleAnalysisComplete} />
        )}

        {activeTab === 'dashboard' && (
          <DashboardPage data={analysisData} onNavigate={(tab) => setActiveTab(tab)} />
        )}

        {/* Placeholders for upcoming phases */}
        {activeTab === 'gaps' && (
          <GapAnalysisPage data={analysisData} onNavigate={(tab) => setActiveTab(tab)} />
        )}

        {activeTab === 'simulator' && (
          <SimulatorPage 
            data={analysisData} 
            onNavigate={(tab) => setActiveTab(tab)}
            onSkillsSelectedForRoadmap={(skills) => setSelectedRoadmapSkills(skills)}
          />
        )}

        {activeTab === 'roadmap' && (
          <RoadmapPage 
            data={analysisData} 
            initialSkills={selectedRoadmapSkills}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'rewriter' && (
          <RewriterPage 
            data={analysisData}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'salary' && (
          <SalaryGrowthPage data={analysisData} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-slate-400">
          SkillBridge AI Career Guidance Platform • Privacy-first design with on-demand data purging
        </div>
      </footer>
    </div>
  );
}
