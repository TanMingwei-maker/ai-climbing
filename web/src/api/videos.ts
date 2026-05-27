import { apiFetch } from './client';

export type VideoRecord = {
  video_id: string;
  filename: string;
  status: string;
};

export function uploadVideo(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  return apiFetch<VideoRecord>('/videos', {
    method: 'POST',
    body: formData,
  });
}

export function getVideo(videoId: string) {
  return apiFetch<VideoRecord>(`/videos/${videoId}`);
}
