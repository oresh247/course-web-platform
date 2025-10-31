"""
Нормализация ответов HeyGen: статусы, download_url, метаданные.
"""
from typing import Dict, Any, Optional


def _extract_download_url(result: Dict[str, Any]) -> Optional[str]:
    data_obj = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    return (
        data_obj.get("video_url")
        or data_obj.get("videoUrl")
        or data_obj.get("download_url")
        or data_obj.get("downloadUrl")
        or data_obj.get("url")
        or data_obj.get("video_file_url")
        or data_obj.get("video_file")
        or result.get("video_url")
        or result.get("videoUrl")
        or result.get("download_url")
        or result.get("downloadUrl")
        or result.get("url")
    )


def normalize_status_response(result: Dict[str, Any], video_id: str) -> Dict[str, Any]:
    status = None
    progress = 0
    download_url = None
    error_details: Any = None

    if isinstance(result, dict):
        if "status" in result:
            status = result.get("status")
            data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
            progress = data.get("progress", 0)
            download_url = _extract_download_url(result)
            if "error" in data:
                error_details = data.get("error", {})
        elif "data" in result:
            data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
            status = data.get("status")
            progress = data.get("progress", 0)
            download_url = _extract_download_url(result)
            if "error" in data:
                error_details = data.get("error", {})
        else:
            status = result.get("status")
            progress = result.get("progress", 0)
            download_url = _extract_download_url(result)
            if "error" in result:
                error_details = result.get("error", {})

    if not status and video_id:
        status = "generating"

    if status == "failed" or error_details:
        error_msg = "Неизвестная ошибка генерации"
        error_code = "unknown"
        if isinstance(error_details, dict):
            error_msg = error_details.get("message", error_msg)
            error_code = error_details.get("code", error_code)
        elif isinstance(error_details, str):
            error_msg = error_details
        return {
            "status": "failed",
            "error": error_msg,
            "error_code": error_code,
            "error_details": error_details,
            "video_id": video_id,
        }

    if status == "generating":
        return {
            "status": "generating",
            "progress": progress or 0,
            "video_id": video_id,
            "estimated_time": result.get("estimated_time") or (result.get("data", {}) if isinstance(result.get("data"), dict) else {}).get("estimated_time"),
        }

    if status == "completed":
        if not download_url and video_id:
            download_url = f"https://resource2.heygen.ai/video/transcode/{video_id}/1280x720.mp4"
        return {
            "status": "completed",
            "progress": 100,
            "video_id": video_id,
            "download_url": download_url,
            "duration": result.get("duration") or (result.get("data", {}) if isinstance(result.get("data"), dict) else {}).get("duration"),
            "file_size": result.get("file_size") or (result.get("data", {}) if isinstance(result.get("data"), dict) else {}).get("file_size"),
        }

    return {
        "status": status or "unknown",
        "progress": progress or 0,
        "video_id": video_id,
        "download_url": download_url,
        "raw_response": result,
    }


