import { fetchClient } from './fetchClient';

export interface EvidenceItem {
  label: string;
  value: string;
}

export interface CopilotResponse {
  answer: string;
  evidence: EvidenceItem[];
  recommended_actions: string[];
  limitations: string[];
}

export interface DecisionCard {
  priority: 'high' | 'medium' | 'low' | string;
  title: string;
  recommended_action: string;
  evidence: string[];
  expected_impact: string;
  confidence: 'high' | 'medium' | 'low' | string;
  limitations: string[];
}

export interface DecisionsResponse {
  decisions: DecisionCard[];
}

export interface ReportSection {
  heading: string;
  content: string;
}

export interface ReportResponse {
  title: string;
  generated_at: string;
  sections: ReportSection[];
  limitations: string[];
}

const intelligenceBase = (workspaceId: string) =>
  `workspaces/${encodeURIComponent(workspaceId)}/intelligence`;

export const askCopilot = async (
  workspaceId: string,
  datasetId: string,
  view: 'mapped' | 'working',
  question: string
): Promise<CopilotResponse> => {
  return fetchClient<CopilotResponse>(
    `${intelligenceBase(workspaceId)}/copilot`,
    {
      method: 'POST',
      body: JSON.stringify({ dataset_id: datasetId, view, question }),
    }
  );
};

export const getDecisions = async (
  workspaceId: string,
  datasetId: string,
  view: 'mapped' | 'working'
): Promise<DecisionsResponse> => {
  return fetchClient<DecisionsResponse>(
    `${intelligenceBase(workspaceId)}/decisions`,
    {
      method: 'POST',
      body: JSON.stringify({ dataset_id: datasetId, view }),
    }
  );
};

export const getReport = async (
  workspaceId: string,
  datasetId: string,
  view: 'mapped' | 'working'
): Promise<ReportResponse> => {
  return fetchClient<ReportResponse>(
    `${intelligenceBase(workspaceId)}/report`,
    {
      method: 'POST',
      body: JSON.stringify({ dataset_id: datasetId, view }),
    }
  );
};
