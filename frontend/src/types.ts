export type ReviewStatus =
  | 'starting'
  | 'running'
  | 'awaiting_approval'
  | 'completed'
  | 'failed'
  | 'aborted';

export type PdfStatus = 'downloaded' | 'abstract_only' | 'not_attempted';

export interface AgentNodeInfo {
  status: 'pending' | 'running' | 'completed' | 'failed';
  summary?: string;
}

export interface ActivityLog {
  timestamp: string;
  agent: string;
  message: string;
}

export interface ReviewOut {
  review_id: string;
  query: string;
  status: ReviewStatus;
  detail: string;
  report_path?: string | null;
  created_at: string;
  node_status?: Record<string, AgentNodeInfo>;
  logs?: ActivityLog[];
}

export interface PaperCandidate {
  index: number;
  title: string;
  year?: number | null;
  score?: number | null;
  reason?: string | null;
  pdf_status: PdfStatus;
}

export interface PendingResponse {
  review_id: string;
  prompt?: string;
  papers: PaperCandidate[];
}

export interface DecisionPayload {
  action: 'approve_all' | 'remove' | 'abort';
  remove?: number[];
}
