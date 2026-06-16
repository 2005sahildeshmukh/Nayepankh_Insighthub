'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useWorkspace } from '@/providers/workspace-provider';
import {
  Menu,
  X,
  ArrowRight,
  Upload,
  MapPin,
  Activity,
  Brain,
  Sparkles,
  Lightbulb,
  FileText,
  Check,
  Loader2
} from 'lucide-react';

export default function RootPage() {
  const router = useRouter();
  const { activeWorkspace, workspaces, isLoading } = useWorkspace();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Helper to handle workspace navigation safely
  const handleLaunch = () => {
    if (activeWorkspace) {
      router.push(`/w/${activeWorkspace.id}`);
    } else if (workspaces.length > 0) {
      router.push(`/w/${workspaces[0].id}`);
    }
  };

  const hasWorkspace = !!(activeWorkspace || workspaces.length > 0);

  // Anchor click helper to smooth scroll and close mobile menu
  const handleAnchorClick = (e: React.MouseEvent<HTMLAnchorElement>, targetId: string) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    const element = document.getElementById(targetId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans selection:bg-indigo-100 selection:text-indigo-900 scroll-smooth">
      {/* Navbar */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="h-9 w-9 rounded-lg bg-indigo-600 flex items-center justify-center shadow-md shadow-indigo-200">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-slate-900 text-lg tracking-tight">NayePankh</span>
              <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wider block -mt-1">InsightHub</span>
            </div>
          </div>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center space-x-8">
            <a
              href="#workflow"
              onClick={(e) => handleAnchorClick(e, 'workflow')}
              className="text-sm font-medium text-slate-600 hover:text-indigo-600 transition-colors"
            >
              Workflow
            </a>
            <a
              href="#features"
              onClick={(e) => handleAnchorClick(e, 'features')}
              className="text-sm font-medium text-slate-600 hover:text-indigo-600 transition-colors"
            >
              Features
            </a>
            <a
              href="#intelligence"
              onClick={(e) => handleAnchorClick(e, 'intelligence')}
              className="text-sm font-medium text-slate-600 hover:text-indigo-600 transition-colors"
            >
              AI Intelligence
            </a>
          </nav>

          <div className="hidden md:flex items-center">
            <button
              onClick={handleLaunch}
              disabled={isLoading || !hasWorkspace}
              className="inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-sm hover:shadow transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Loading...
                </>
              ) : (
                'Open InsightHub'
              )}
            </button>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label={mobileMenuOpen ? 'Close Menu' : 'Open Menu'}
              aria-expanded={mobileMenuOpen}
              className="inline-flex items-center justify-center p-2 rounded-md text-slate-500 hover:text-slate-600 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-slate-200 bg-white px-4 pt-2 pb-4 space-y-1">
            <a
              href="#workflow"
              onClick={(e) => handleAnchorClick(e, 'workflow')}
              className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50 hover:text-indigo-600"
            >
              Workflow
            </a>
            <a
              href="#features"
              onClick={(e) => handleAnchorClick(e, 'features')}
              className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50 hover:text-indigo-600"
            >
              Features
            </a>
            <a
              href="#intelligence"
              onClick={(e) => handleAnchorClick(e, 'intelligence')}
              className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50 hover:text-indigo-600"
            >
              AI Intelligence
            </a>
            <div className="pt-4 pb-2 border-t border-slate-100">
              <button
                onClick={handleLaunch}
                disabled={isLoading || !hasWorkspace}
                className="w-full inline-flex items-center justify-center px-4 py-3 text-base font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-sm transition-all"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Loading...
                  </>
                ) : (
                  'Open InsightHub'
                )}
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 lg:py-32 bg-gradient-to-b from-indigo-50/50 via-white to-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-100 mb-6 uppercase tracking-wider">
            AI-Powered NGO Intelligence
          </span>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight">
            From Raw NGO Data to <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">Actionable Intelligence</span>
          </h1>
          <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
            Upload datasets, clean and profile them, discover trends, train predictive models, ask AI questions, and generate decision-ready reports—all from one intelligent workspace.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={handleLaunch}
              disabled={isLoading || !hasWorkspace}
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 text-base font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-md shadow-indigo-200 hover:shadow-lg transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  Loading workspace...
                </>
              ) : (
                <>
                  Launch Workspace
                  <ArrowRight className="ml-2 h-5 w-5" />
                </>
              )}
            </button>
            <a
              href="#features"
              onClick={(e) => handleAnchorClick(e, 'features')}
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 text-base font-semibold text-slate-700 hover:text-slate-900 bg-white border border-slate-200 hover:border-slate-300 rounded-xl transition-all shadow-sm"
            >
              Explore Features
            </a>
          </div>
        </div>
      </section>

      {/* Workflow Section */}
      <section id="workflow" className="py-16 bg-white border-y border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-slate-900 text-center tracking-tight mb-12">
            The Data Intelligence Workflow
          </h2>
          <div className="flex flex-col lg:flex-row items-stretch justify-between gap-4">
            {[
              { label: 'Upload', desc: 'Secure data ingestion' },
              { label: 'Map', desc: 'Align schema & fields' },
              { label: 'Clean', desc: 'Fix missing values & issues' },
              { label: 'Analyze', desc: 'Discover patterns' },
              { label: 'Predict', desc: 'AutoML intelligence' },
              { label: 'Decide', desc: 'Context-driven guidance' },
              { label: 'Report', desc: 'Decision-ready metrics' }
            ].map((step, idx, arr) => (
              <React.Fragment key={step.label}>
                <div className="flex-1 bg-slate-50 border border-slate-200/60 rounded-xl p-5 flex flex-col items-center text-center justify-center shadow-sm relative group hover:border-indigo-200 hover:bg-indigo-50/10 transition-all">
                  <span className="h-8 w-8 rounded-full bg-indigo-50 text-indigo-600 font-semibold text-sm flex items-center justify-center border border-indigo-100 group-hover:bg-indigo-600 group-hover:text-white transition-all">
                    {idx + 1}
                  </span>
                  <h3 className="font-bold text-slate-800 mt-3 text-base">{step.label}</h3>
                  <p className="text-xs text-slate-500 mt-1">{step.desc}</p>
                </div>
                {idx < arr.length - 1 && (
                  <div className="hidden lg:flex items-center justify-center text-slate-300">
                    <ArrowRight className="h-5 w-5" />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
              Comprehensive Features for Impact
            </h2>
            <p className="text-slate-600 mt-4">
              Everything you need to handle NGO program data and drive intelligence-backed decisions in a unified workspace.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[
              {
                title: 'Smart Data Upload & Mapping',
                desc: 'Upload CSV datasets with auto-detected columns and map program schemas cleanly.',
                icon: Upload
              },
              {
                title: 'Data Profiling & Cleaning',
                desc: 'Detect errors, visualize missing value distributions, and design optimal cleaning policies.',
                icon: MapPin
              },
              {
                title: 'Interactive Analytics',
                desc: 'Run detailed breakdowns and view dynamically generated charts instantly.',
                icon: Activity
              },
              {
                title: 'AutoML Studio',
                desc: 'Train prediction models, perform hyperparameter tuning, and evaluate model performance.',
                icon: Brain
              },
              {
                title: 'AI Copilot',
                desc: 'Interact with your datasets using natural language queries powered by AI assistance.',
                icon: Sparkles
              },
              {
                title: 'Decision Intelligence',
                desc: 'Receive context-aware scenario evaluation, strategic suggestions, and outcome predictions.',
                icon: Lightbulb
              },
              {
                title: 'Executive Reports',
                desc: 'Generate, preview, and export comprehensive summaries for key stakeholders.',
                icon: FileText
              }
            ].map((feat) => {
              const Icon = feat.icon;
              return (
                <div
                  key={feat.title}
                  className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-md hover:border-slate-300 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="h-10 w-10 bg-indigo-50 border border-indigo-100 rounded-xl flex items-center justify-center text-indigo-600 mb-5">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h3 className="font-bold text-slate-900 text-base leading-snug">{feat.title}</h3>
                    <p className="text-sm text-slate-500 mt-2 leading-relaxed">{feat.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* AI Intelligence Section */}
      <section id="intelligence" className="py-24 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:grid lg:grid-cols-2 lg:gap-16 items-center">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">Advanced AI Core</span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mt-2">
                Unified Analytical Models
              </h2>
              <p className="mt-4 text-slate-600 text-base leading-relaxed">
                NayePankh InsightHub leverages advanced predictive models and language reasoning capabilities to bridge the gap between complex datasets and human strategic understanding.
              </p>
              
              <div className="mt-8 space-y-4">
                {[
                  'Contextual mapping of unstructured fields',
                  'Anomaly and error pattern detection',
                  'Scenario simulations and outcome calculations',
                  'Automatic query and analytics generation',
                  'Instant synthesis into decision-ready reports'
                ].map((point) => (
                  <div key={point} className="flex items-start">
                    <div className="flex-shrink-0 h-5 w-5 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 mt-0.5">
                      <Check className="h-3 w-3" />
                    </div>
                    <span className="ml-3 text-sm text-slate-700 font-medium">{point}</span>
                  </div>
                ))}
              </div>

              <p className="text-xs text-slate-400 font-medium mt-8 flex items-center">
                <Sparkles className="h-4 w-4 mr-2 text-indigo-500" />
                Powered by Gemini
              </p>
            </div>
            
            <div className="mt-12 lg:mt-0 bg-slate-50 border border-slate-200 rounded-3xl p-8 shadow-inner relative overflow-hidden">
              <div className="space-y-4">
                <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm max-w-md">
                  <p className="text-xs font-bold text-indigo-600 uppercase tracking-wider">AI Insight Generator</p>
                  <p className="text-sm text-slate-700 mt-1 font-medium italic">
                    &ldquo;Based on AutoML modeling, a 15% increase in mentor check-ins is projected to improve student retention by up to 22% in sub-districts showing higher initial drop-out patterns.&rdquo;
                  </p>
                </div>
                <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm max-w-md ml-auto">
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Cleaned Fields Analysis</p>
                  <p className="text-sm text-slate-700 mt-1">
                    Mapped 4,200 raw data rows, resolved 112 invalid category entries, and calculated confidence scores for student registration timestamps.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="py-20 bg-slate-900 relative overflow-hidden">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Turn Your Data Into Decisions
          </h2>
          <p className="mt-4 text-slate-400 text-base max-w-xl mx-auto">
            Get started with NayePankh InsightHub to profile, clean, model, and unlock the value hidden inside your program files.
          </p>
          <div className="mt-8">
            <button
              onClick={handleLaunch}
              disabled={isLoading || !hasWorkspace}
              className="inline-flex items-center justify-center px-6 py-3.5 text-base font-semibold text-slate-900 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-md transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin text-indigo-600" />
                  Connecting...
                </>
              ) : (
                'Open NayePankh InsightHub'
              )}
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-200 bg-white py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <span className="font-bold text-slate-950 text-base">NayePankh InsightHub</span>
            <p className="text-xs text-slate-500 mt-1">Built for smarter, data-driven NGO program execution.</p>
          </div>
          <p className="text-xs text-slate-400 font-medium">
            &copy; {new Date().getFullYear()} NayePankh. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
