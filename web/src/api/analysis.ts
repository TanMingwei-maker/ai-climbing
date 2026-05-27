import { apiFetch } from './client';

export type AnalysisTaskResponse = {
  task_id: string;
  video_id: string;
  status: string;
  message: string;
  result_json_url?: string | null;
  result_video_url?: string | null;
};

export function startAnalysis(videoId: string) {
  return apiFetch<AnalysisTaskResponse>(`/videos/${videoId}/analyze`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}
