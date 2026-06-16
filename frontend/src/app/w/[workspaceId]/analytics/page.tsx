"use client";

import React from 'react';
import { useParams } from 'next/navigation';
import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard';

export default function AnalyticsPage() {
  const routeParams = useParams<{ workspaceId: string }>();

  return (
    <div className="w-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Analytics Workspace</h1>
        <p className="text-slate-600 mt-1 text-sm">
          Explore data, monitor KPIs, and generate dynamic visualizations.
        </p>
      </div>

      <AnalyticsDashboard workspaceId={routeParams.workspaceId} />
    </div>
  );
}
