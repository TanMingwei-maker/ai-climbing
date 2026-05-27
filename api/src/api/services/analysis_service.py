from __future__ import annotations

import json
import sys
import traceback
import urllib.request
import uuid
from pathlib import Path

from api.config import ANNOTATION_DIR, OUTPUT_DIR, PROJECT_ROOT
from api.repositories.video_repo import get_video, update_analysis_result
from api.schemas.result import AnalysisResultResponse
from api.schemas.task import AnalysisTaskResponse
from api.services.video_service import get_video_source_path

SRC_DIR = PROJECT_ROOT / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_climbing.pose_pipeline import ClimbingPoseAnalyzer


# #region debug-point log-helper
def _debug_report(hypothesis_id: str, msg: str, data: dict[str, object]) -> None:
    _p = ".dbg/analyze-500-error.env"
    _u, _s = "http://127.0.0.1:7777/event", "analyze-500-error"
    try:
        with open(_p, encoding="utf-8") as _f:
            _c = _f.read()
        _u = next((line.split("=", 1)[1] for line in _c.splitlines() if line.startswith("DEBUG_SERVER_URL=")), _u)
        _s = next((line.split("=", 1)[1] for line in _c.splitlines() if line.startswith("DEBUG_SESSION_ID=")), _s)
    except OSError:
        pass
    try:
        urllib.request.urlopen(
            urllib.request.Request(
                _u,
                data=json.dumps(
                    {
                        "sessionId": _s,
                        "runId": "pre-fix",
                        "hypothesisId": hypothesis_id,
                        "location": "api/src/api/services/analysis_service.py",
                        "msg": f"[DEBUG] {msg}",
                        "data": data,
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
            )
        ).read()
    except Exception:
        pass


# #endregion


def create_analysis_task(video_id: str) -> AnalysisTaskResponse:
    video_record = get_video(video_id)
    video_path = get_video_source_path(video_id)
    # #region debug-point B:video-record
    _debug_report(
        "B",
        "resolved video record before analysis",
        {
            "video_id": video_id,
            "video_exists": bool(video_record),
            "video_path": str(video_path) if video_path else None,
            "video_path_exists": video_path.exists() if video_path else False,
        },
    )
    # #endregion
    if video_record is None or video_path is None or not video_path.exists():
        raise FileNotFoundError(f"video not found: {video_id}")

    annotation_path = ANNOTATION_DIR / f'{video_id}.route_context.json'
    output_prefix = OUTPUT_DIR / video_id
    output_prefix.mkdir(parents=True, exist_ok=True)
    output_video = output_prefix / f"{video_id}.annotated.mp4"
    output_json = output_prefix / f"{video_id}.analysis.json"
    # #region debug-point C:paths-ready
    _debug_report(
        "C",
        "prepared analysis paths",
        {
            "annotation_path": str(annotation_path),
            "annotation_exists": annotation_path.exists(),
            "output_video": str(output_video),
            "output_json": str(output_json),
        },
    )
    # #endregion

    analyzer = ClimbingPoseAnalyzer()
    # #region debug-point A:analyze-video
    _debug_report("A", "starting analyzer.analyze_video", {"video_id": video_id})
    # #endregion
    try:
        analyzer.analyze_video(
            input_path=video_path,
            output_video_path=output_video,
            output_json_path=output_json,
            route_context_path=annotation_path if annotation_path.exists() else None,
        )
    except Exception as exc:
        # #region debug-point D:analyze-error
        _debug_report(
            "D",
            "analyze_video raised exception",
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        # #endregion
        raise
    # #region debug-point E:analyze-success
    _debug_report(
        "E",
        "analyze_video finished successfully",
        {
            "output_video_exists": output_video.exists(),
            "output_json_exists": output_json.exists(),
        },
    )
    # #endregion
    update_analysis_result(
        video_id=video_id,
        status="succeeded",
        annotation_path=annotation_path if annotation_path.exists() else None,
        result_json_path=output_json,
        result_video_path=output_video,
    )

    return AnalysisTaskResponse(
        task_id=f'task_{uuid.uuid4().hex[:8]}',
        video_id=video_id,
        status='succeeded',
        message='分析完成',
        result_json_url=f"/static/outputs/{video_id}/{output_json.name}",
        result_video_url=f"/static/outputs/{video_id}/{output_video.name}",
    )


def get_analysis_result(video_id: str) -> AnalysisResultResponse:
    video_record = get_video(video_id)
    if (
        video_record is None
        or not video_record.result_video_path
        or not video_record.result_json_path
    ):
        raise FileNotFoundError(f"result not found: {video_id}")

    video_path = Path(video_record.result_video_path)
    json_path = Path(video_record.result_json_path)
    if not video_path.exists() or not json_path.exists():
        raise FileNotFoundError(f"result not found: {video_id}")

    return AnalysisResultResponse(
        video_id=video_id,
        status="succeeded",
        result_json_url=f"/static/outputs/{video_id}/{json_path.name}",
        result_video_url=f"/static/outputs/{video_id}/{video_path.name}",
    )
