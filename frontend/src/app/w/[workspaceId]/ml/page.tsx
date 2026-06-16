'use client';

import React from 'react';
import { useWorkspace } from '@/providers/workspace-provider';
import MlStudio from '@/components/ml/MlStudio';

export default function MLPage() {
  const { activeWorkspace, isLoading } = useWorkspace();

  if (isLoading || !activeWorkspace) return null;

  return (
    <div className="h-full">
      <MlStudio />
    </div>
  );
}
