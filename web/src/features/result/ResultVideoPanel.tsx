import { Link } from 'react-router-dom';

type ResultVideoPanelProps = {
  videoId: string;
  status: string;
  videoUrl: string | null;
  hasResult: boolean;
};

export function ResultVideoPanel({ videoId, status, videoUrl, hasResult }: ResultVideoPanelProps) {
  return (
    <section className="panel">
      <p className="eyebrow">结果视频</p>
      <h1>{videoId}</h1>
      <p className="muted">{status}</p>
      <div className="button-row">
        <Link className="ghost-button" to={`/videos/${videoId}`}>
          返回概览页
        </Link>
        <Link className="ghost-button" to={`/annotate/${videoId}`}>
          返回标注页
        </Link>
        <Link className="ghost-button" to={`/analyze/${videoId}`}>
          去分析页
        </Link>
      </div>
      {!hasResult ? (
        <div className="notice-card">
          <strong>结果暂不可用</strong>
          <p className="muted">当前视频还没有生成分析结果，可以先回到标注页补充人工点位，再重新启动分析。</p>
        </div>
      ) : null}
      {videoUrl ? (
        <video className="result-video" controls src={videoUrl} />
      ) : (
        <div className="video-placeholder">分析完成后，这里会显示标注视频</div>
      )}
    </section>
  );
}
