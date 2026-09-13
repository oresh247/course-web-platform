"""Black-box smoke-проверка запущенного local demo-сервера Course Brief."""
import argparse
import json
import sys
from typing import Any, Dict, Tuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request_json(
    base_url: str,
    path: str,
    method: str = "GET",
    body: Dict[str, Any] | None = None,
) -> Tuple[int, Dict[str, Any]]:
    data = (
        json.dumps(body, ensure_ascii=False).encode("utf-8")
        if body is not None
        else None
    )
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        payload = error.read().decode("utf-8")
        return error.code, json.loads(payload) if payload else {}


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ensure_safe_response(payload: Dict[str, Any]) -> None:
    ensure(
        "preliminary_outline" not in payload,
        "Черновая структура попала в API-ответ",
    )
    ensure(
        "decisions" not in payload,
        "Внутренние решения попали в API-ответ",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    status, health = request_json(args.base_url, "/api/health")
    ensure(
        status == 200 and health.get("demo_mode") is True,
        "Не найден локальный demo-сервер",
    )

    status, state = request_json(
        args.base_url,
        "/api/course-briefs/",
        "POST",
        {"topic": "Python для аналитики данных"},
    )
    ensure(
        status == 201,
        f"Старт интервью вернул {status}: {state}",
    )
    ensure_safe_response(state)
    ensure(
        state["status"] == "questioning",
        "Интервью должно ожидать ответа",
    )
    ensure(
        state["progress"]["percentage"] == 0,
        "Стартовый прогресс должен быть 0%",
    )
    ensure(state.get("question"), "Первый вопрос не получен")

    session_id = state["session_id"]
    initial_revision = state["revision"]
    state_path = f"/api/course-briefs/{session_id}"
    status, restored = request_json(args.base_url, state_path)
    ensure(
        status == 200,
        f"Состояние интервью недоступно: {restored}",
    )
    ensure_safe_response(restored)

    status, state = request_json(
        args.base_url,
        f"/api/course-briefs/{session_id}/answers",
        "POST",
        {
            "expected_revision": initial_revision,
            "depth": "standard",
            "knowledge_level": "middle",
        },
    )
    ensure(
        status == 200,
        f"Первый ответ не принят: {state}",
    )
    ensure_safe_response(state)
    ensure(
        state["progress"]["percentage"] > 0,
        "Прогресс не увеличился после ответа",
    )

    stale_status, _ = request_json(
        args.base_url,
        f"/api/course-briefs/{session_id}/answers",
        "POST",
        {"expected_revision": initial_revision, "depth": "deep"},
    )
    ensure(
        stale_status == 409,
        "Устаревший ответ должен быть отклонён с 409",
    )

    depths = ("brief", "skip", "deep")
    depth_index = 0
    while state["status"] == "questioning":
        status, state = request_json(
            args.base_url,
            f"/api/course-briefs/{session_id}/answers",
            "POST",
            {
                "expected_revision": state["revision"],
                "depth": depths[depth_index % len(depths)],
                "knowledge_level": "junior",
            },
        )
        ensure(
            status == 200,
            f"Ответ интервью не принят: {state}",
        )
        ensure_safe_response(state)
        depth_index += 1

    ensure(
        state["status"] == "completed",
        "Интервью не завершилось",
    )
    ensure(
        state["progress"]["percentage"] == 100,
        "Финальный прогресс должен быть 100%",
    )
    ensure(
        state.get("final_course"),
        "Финальная структура не получена",
    )
    ensure(
        state["final_course"].get("modules"),
        "В финальной структуре нет модулей",
    )
    print("PASS: локальный Course Brief MVP")
    print("API, прогресс, CAS и скрытый черновик")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, KeyError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
