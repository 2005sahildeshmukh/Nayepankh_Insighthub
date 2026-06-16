'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useWorkspace } from '@/providers/workspace-provider';
import { LayoutDashboard, Database, Brain, BarChart, Sparkles, Lightbulb, FileText } from 'lucide-react';
import clsx from 'clsx';

export function Sidebar() {
  const pathname = usePathname();
  const { activeWorkspace, isLoading } = useWorkspace();

  if (isLoading || !activeWorkspace) {
    return <div className="w-64 border-r border-slate-200 bg-slate-50 min-h-screen p-4 flex flex-col animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-3/4 mb-8"></div>
        <div className="space-y-4">
            <div className="h-4 bg-slate-200 rounded w-full"></div>
            <div className="h-4 bg-slate-200 rounded w-full"></div>
            <div className="h-4 bg-slate-200 rounded w-full"></div>
        </div>
    </div>;
  }

  const navItems = [
    { name: 'Dashboard', href: `/w/${activeWorkspace.id}`, icon: LayoutDashboard },
    { name: 'Datasets', href: `/w/${activeWorkspace.id}/datasets`, icon: Database },
    { name: 'Analytics', href: `/w/${activeWorkspace.id}/analytics`, icon: BarChart },
    { name: 'Machine Learning', href: `/w/${activeWorkspace.id}/ml`, icon: Brain },
    { name: 'AI Copilot', href: `/w/${activeWorkspace.id}/copilot`, icon: Sparkles },
    { name: 'Decision Intelligence', href: `/w/${activeWorkspace.id}/decision`, icon: Lightbulb },
    { name: 'Reports', href: `/w/${activeWorkspace.id}/reports`, icon: FileText },
  ];

  return (
    <div className="w-64 border-r border-slate-200 bg-white flex flex-col h-screen overflow-y-auto">
      <div className="p-6">
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">NayePankh</h1>
        <p className="text-xs text-slate-500 font-medium mt-1 uppercase tracking-wider">InsightHub</p>
      </div>

      <nav className="flex-1 px-4 space-y-1 mt-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors group',
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              )}
            >
              <Icon
                className={clsx(
                  'mr-3 h-5 w-5 flex-shrink-0 transition-colors',
                  isActive ? 'text-blue-700' : 'text-slate-400 group-hover:text-slate-500'
                )}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-200">
        <div className="truncate">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Workspace</p>
          <p className="text-sm font-medium text-slate-700 truncate mt-0.5">{activeWorkspace.name}</p>
        </div>
      </div>
    </div>
  );
}
