'use client';

import React from 'react';
import { WorkspaceProvider } from './workspace-provider';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <WorkspaceProvider>
        {children}
      </WorkspaceProvider>
    </QueryClientProvider>
  );
}
