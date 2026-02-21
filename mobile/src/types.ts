export interface FunctionCall {
  name: string;
  arguments: Record<string, unknown>;
}

export interface AnalysisData {
  confidence: number;
  local_time_ms: number;
  function_calls: FunctionCall[];
  recommendation: 'local' | 'cloud';
  threshold: number;
}

export interface ResultData {
  source: string;
  total_time_ms?: number;
  confidence?: number;
  function_calls?: FunctionCall[];
  error?: string;
}

export type Message =
  | { id: string; type: 'user'; text: string }
  | { id: string; type: 'loading' }
  | { id: string; type: 'error'; text: string }
  | { id: string; type: 'analysis'; data: AnalysisData; originalMsg: string; locked: boolean }
  | { id: string; type: 'result'; data: ResultData; originalMsg: string };
