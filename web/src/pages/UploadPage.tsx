import { useMutation } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getApiErrorMessage } from '../api/client';
import { uploadVideo } from '../api/videos';

export function UploadPage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [status, setStatus] = useState('支持 mp4 / mov，上传后会先进入视频概览页。');

  const uploadMutation = useMutation({
    mutationFn: uploadVideo,
    onSuccess: (record) => {
      setStatus(`上传完成，正在跳转到 ${record.video_id}`);
      navigate(`/videos/${record.video_id}`);
    },
    onError: (error) => {
      setStatus(getApiErrorMessage(error, '上传失败，请稍后再试'));
    },
    onSettled: () => {
      if (inputRef.current) {
        inputRef.current.value = '';
      }
    },
  });

  const handleUpload = async (file: File | null) => {
    if (!file) {
      return;
    }

    setStatus(`正在上传 ${file.name} ...`);
    await uploadMutation.mutateAsync(file);
  };

  return (
    <main className="page">
      <section className="panel hero-panel">
        <p className="eyebrow">AI Climbing</p>
        <h1>上传攀岩视频</h1>
        <p className="muted">{status}</p>
        <div className="button-row">
          <button
            className="primary-button"
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={uploadMutation.isPending}
          >
            {uploadMutation.isPending ? '上传中...' : '选择视频并上传'}
          </button>
          <Link className="ghost-button" to="/annotate/demo-video">查看标注页骨架</Link>
        </div>
        <input
          ref={inputRef}
          className="hidden-input"
          type="file"
          accept="video/mp4,video/quicktime,video/*"
          onChange={(event) => void handleUpload(event.target.files?.[0] ?? null)}
        />
      </section>
    </main>
  );
}
