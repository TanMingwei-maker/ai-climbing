import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { getRouteContext } from '../api/annotations';
import { getApiErrorMessage, isApiError } from '../api/client';
import { getAnalysisResult } from '../api/results';
import { getVideo } from '../api/videos';

function formatAngle(angle?: number | null) {
  if (angle == null || Number.isNaN(angle)) {
    return '-';
  }
  return `${angle} 度`;
}

async function getOptionalResult(videoId: string) {
  try {
    return await getAnalysisResult(videoId);
  } catch (error) {
    if (isApiError(error) && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function VideoOverviewPage() {
  const { videoId = 'demo-video' } = useParams();
  const videoQuery = useQuery({
    queryKey: ['video', videoId],
    queryFn: () => getVideo(videoId),
  });
  const routeContextQuery = useQuery({
    queryKey: ['route-context', videoId],
    queryFn: () => getRouteContext(videoId),
  });
  const resultQuery = useQuery({
    queryKey: ['analysis-result', videoId],
    queryFn: () => getOptionalResult(videoId),
    retry: false,
  });

  const hasRouteContext = (routeContextQuery.data?.holds.length ?? 0) > 0;
  const hasResult = Boolean(resultQuery.data);
  const isPending = videoQuery.isPending || routeContextQuery.isPending || resultQuery.isPending;
  const errorMessage = videoQuery.error
    ? getApiErrorMessage(videoQuery.error, '视频信息加载失败')
    : routeContextQuery.error
      ? getApiErrorMessage(routeContextQuery.error, '路线标注加载失败')
      : resultQuery.error
        ? getApiErrorMessage(resultQuery.error, '分析结果加载失败')
        : null;

  return (
    <main className="page">
      <section className="panel">
        <p className="eyebrow">视频概览</p>
        <h1>{videoId}</h1>
        <p className="muted">
          {isPending
            ? '正在加载视频状态...'
            : errorMessage ?? '在这里继续标注、启动分析，或查看最近一次分析结果。'}
        </p>

        {videoQuery.data ? (
          <div className="result-grid overview-grid">
            <div className="overview-stat">
              <span className="result-label">文件名</span>
              <strong>{videoQuery.data.filename}</strong>
            </div>
            <div className="overview-stat">
              <span className="result-label">视频状态</span>
              <strong>{videoQuery.data.status}</strong>
            </div>
            <div className="overview-stat">
              <span className="result-label">路线名</span>
              <strong>{routeContextQuery.data?.route.name || '未命名路线'}</strong>
            </div>
            <div className="overview-stat">
              <span className="result-label">墙面</span>
              <strong>{routeContextQuery.data?.wall.name || '默认墙面'}</strong>
            </div>
            <div className="overview-stat">
              <span className="result-label">角度</span>
              <strong>{formatAngle(routeContextQuery.data?.wall.angle_deg)}</strong>
            </div>
            <div className="overview-stat">
              <span className="result-label">人工点位</span>
              <strong>{routeContextQuery.data?.holds.length ?? 0}</strong>
            </div>
          </div>
        ) : null}

        <div className="overview-card-grid">
          <section className="result-card">
            <h2>标注状态</h2>
            <p className="muted">
              {hasRouteContext ? '已存在路线标注，可继续编辑或直接进入分析。' : '当前还没有可用路线标注。'}
            </p>
            <div className="button-row">
              <Link className="primary-button" to={`/annotate/${videoId}`}>
                {hasRouteContext ? '继续标注' : '开始标注'}
              </Link>
            </div>
          </section>

          <section className="result-card">
            <h2>分析状态</h2>
            <p className="muted">
              {hasResult
                ? '已存在最近一次分析结果，可直接查看或重新分析。'
                : hasRouteContext
                  ? '已具备分析前提，可以启动分析。'
                  : '请先完成路线标注，再开始分析。'}
            </p>
            <div className="button-row">
              <Link
                className={hasRouteContext ? 'primary-button' : 'ghost-button'}
                to={hasRouteContext ? `/analyze/${videoId}` : `/annotate/${videoId}`}
              >
                {hasRouteContext ? '进入分析' : '先去标注'}
              </Link>
              {hasResult ? (
                <Link className="ghost-button" to={`/result/${videoId}`}>
                  查看结果
                </Link>
              ) : null}
            </div>
          </section>
        </div>

        <div className="button-row">
          <Link className="ghost-button" to="/">
            返回上传页
          </Link>
        </div>
      </section>
    </main>
  );
}
