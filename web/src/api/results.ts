import { apiFetch } from './client';

export type AnalysisResultResponse = {
  video_id: string;
  status: string;
  result_json_url: string;
  result_video_url: string;
};

export function getAnalysisResult(videoId: string) {
  return apiFetch<AnalysisResultResponse>(`/videos/${videoId}/result`);
}
