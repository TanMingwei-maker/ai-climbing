import { apiFetch } from './client';

export type FrameExtractResponse = {
  video_id: string;
  frame_name: string;
  frame_url: string;
  width: number;
  height: number;
  frame_index: number;
  status: string;
};

export function extractFrame(videoId: string, frameIndex?: number) {
  return apiFetch<FrameExtractResponse>(`/videos/${videoId}/frames/extract`, {
    method: 'POST',
    body: JSON.stringify(frameIndex === undefined ? {} : { frame_index: frameIndex }),
  });
}
