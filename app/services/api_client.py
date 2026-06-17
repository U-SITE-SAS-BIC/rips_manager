import httpx
import json
from typing import Optional


async def send_json(
    url: str,
    json_data: dict,
    method: str = "POST",
    headers: Optional[dict] = None,
    timeout: int = 30,
) -> dict:
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method == "POST":
                resp = await client.post(url, json=json_data, headers=default_headers)
            elif method == "PUT":
                resp = await client.put(url, json=json_data, headers=default_headers)
            else:
                resp = await client.get(url, headers=default_headers)

            return {
                "status_code": resp.status_code,
                "success": resp.is_success,
                "body": resp.text,
                "headers": dict(resp.headers),
            }
    except httpx.TimeoutException:
        return {"status_code": 0, "success": False, "body": "Timeout", "headers": {}}
    except Exception as e:
        return {"status_code": 0, "success": False, "body": str(e), "headers": {}}
