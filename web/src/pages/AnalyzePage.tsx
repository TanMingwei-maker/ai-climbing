import { useMutation, useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { startAnalysis } from '../api/analysis';
import { getRouteContext } from '../api/annotations';
import { getApiErrorMessage, isApiError } from '../api/client';
import { getAnalysisResult } from '../api/results';
import { getVideo } from '../api/videos';

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

export function AnalyzePage() {
  const { videoId = 'demo-video' } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('待启动');
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
  const analyzeMutation = useMutation({
    mutationFn: () => startAnalysis(videoId),
    onSuccess: (result) => {
      setStatus(result.message);
      navigate(`/result/${videoId}`);
    },
    onError: (error) => {
      setStatus(getApiErrorMessage(error, '分析失败，请稍后再试'));
    },
  });

  const isLoading = videoQuery.isPending || routeContextQuery.isPending || resultQuery.isPending;
  const errorMessage = videoQuery.error
    ? getApiErrorMessage(videoQuery.error, '视频信息加载失败')
    : routeContextQuery.error
      ? getApiErrorMessage(routeContextQuery.error, '标注信息加载失败')
      : resultQuery.error
        ? getApiErrorMessage(resultQuery.error, '结果状态加载失败')
        : null;
  const holdCount = routeContextQuery.data?.holds.length ?? 0;
  const hasRouteContext = holdCount > 0;

  const handleAnalyze = async () => {
    setStatus('正在执行分析，首次运行可能需要一点时间...');
    await analyzeMutation.mutateAsync();
  };

  return (
    <main className="page">
      <section className="panel">
        <p className="eyebrow">分析页</p>
        <h1>准备分析 {videoId}</h1>
        <p className="muted">
          {isLoading
            ? '正在加载分析前置条件...'
            : errorMessage ?? '当前将直接调用后端分析服务，并在完成后跳转到结果页。'}
        </p>
        <div className="result-grid overview-grid">
          <div className="overview-stat">
            <span className="result-label">文件名</span>
            <strong>{videoQuery.data?.filename ?? '-'}</strong>
          </div>
          <div className="overview-stat">
            <span className="result-label">视频状态</span>
            <strong>{videoQuery.data?.status ?? '-'}</strong>
          </div>
          <div className="overview-stat">
            <span className="result-label">路线名</span>
            <strong>{routeContextQuery.data?.route.name || '未命名路线'}</strong>
          </div>
          <div className="overview-stat">
            <span className="result-label">人工点位</span>
            <strong>{holdCount}</strong>
          </div>
        </div>
        <div className="status-card">
          <span className="status-dot" />
          <span>任务状态：{status}</span>
        </div>
        {!isLoading && !errorMessage && !hasRouteContext ? (
          <div className="notice-card">
            <strong>还不能开始分析</strong>
            <p className="muted">当前视频还没有有效的路线标注，请先到标注页保存至少一个人工点位。</p>
          </div>
        ) : null}
        <div className="button-row">
          <button
            className="primary-button"
            type="button"
            onClick={() => void handleAnalyze()}
            disabled={analyzeMutation.isPending || isLoading || Boolean(errorMessage) || !hasRouteContext}
          >
            {analyzeMutation.isPending ? '分析中...' : '启动分析'}
          </button>
          <Link className="ghost-button" to={`/annotate/${videoId}`}>
            返回标注页
          </Link>
          {resultQuery.data ? (
            <Link className="ghost-button" to={`/result/${videoId}`}>
              查看结果页
            </Link>
          ) : null}
          <Link className="ghost-button" to={`/videos/${videoId}`}>
            返回概览页
          </Link>
        </div>
      </section>
    </main>
  );
}
