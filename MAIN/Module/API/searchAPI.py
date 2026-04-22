import json
from typing import Any, Dict, List, Optional

import requests

from MAIN.Connection.dgov_conn import api_key

BASE_URL = "https://api.odcloud.kr/api/GetSearchDataList/v1/searchData"


def search_korean_data_portal(
    *,
    service_key: str = "",          # <-- leave blank; paste your key here manually
    authorization: str = "",        # <-- optional: some keys are used as Authorization header instead
    keyword: str = "",
    page: int = 1,
    size: int = 10,
    data_types: Optional[List[str]] = None,  # e.g., ["FILE", "API", "STD"]
    timeout_sec: int = 30,
) -> Dict[str, Any]:
    """
    Calls 공공데이터포털 검색 서비스 (POST JSON).
    Auth supports either:
      - query param: serviceKey=...
      - header: Authorization: ...
    You can set either (or both) depending on how your key is issued.
    """
    if data_types is None:
        data_types = ["FILE", "API", "STD"]

    payload: Dict[str, Any] = {
        "page": page,
        "size": size,
        "dataType": data_types,
    }
    if keyword:
        payload["keyword"] = keyword

    headers = {
        "Content-Type": "application/json",
    }
    if authorization:
        headers["Authorization"] = authorization

    params = {}
    if service_key:
        params["serviceKey"] = service_key  # securityDefinitions: ApiKeyAuth2 (in=query)

    resp = requests.post(
        BASE_URL,
        headers=headers,
        params=params,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=timeout_sec,
    )

    # Raise on HTTP errors (401/400/500 etc.)
    resp.raise_for_status()

    # Most responses should be JSON
    return resp.json()


def print_search_results(api_json: Dict[str, Any], *, max_items: int = 10) -> None:
    """
    Prints a human-readable summary of the response.
    Expected shape (based on your swagger):
      { "statusCode": int, "result": [ { "sum": int, "dataCount": int, "data": [ ... ] } ] }
    """
    status_code = api_json.get("statusCode")
    print(f"statusCode: {status_code}")

    result_list = api_json.get("result") or []
    if not result_list:
        print("No 'result' in response (or empty). Full response:")
        print(json.dumps(api_json, ensure_ascii=False, indent=2))
        return

    first = result_list[0] if isinstance(result_list, list) else result_list
    total_sum = first.get("sum")
    data_count = first.get("dataCount")
    data_items = first.get("data") or []

    print(f"total sum: {total_sum}")
    print(f"returned dataCount: {data_count}")
    print(f"items in 'data': {len(data_items)}")
    print("-" * 80)

    for i, item in enumerate(data_items[:max_items], start=1):
        name = item.get("dataName", "")
        org = item.get("organization", "")
        dtype = item.get("dataType", "")
        provision = item.get("dataProvisionType", "")
        update = item.get("updateDate", "")
        url = item.get("detailPageUrl", "")

        desc = (item.get("dataDescription") or "").strip()
        if len(desc) > 180:
            desc = desc[:180] + "..."

        print(f"[{i}] {name}")
        print(f"    org: {org} | dataType: {dtype} | serviceType: {provision} | updateDate: {update}")
        if url:
            print(f"    url: {url}")
        if desc:
            print(f"    desc: {desc}")
        print()


if __name__ == "__main__":
    # Example call (leave keys blank here; paste your key where appropriate)
    # - If your key is meant for query param:
    #     service_key="PASTE_YOUR_KEY"
    # - If your key is meant for Authorization header:
    #     authorization="PASTE_YOUR_KEY"
    #
    # You can also set both if unsure; the server will use what it expects.

    try:
        data = search_korean_data_portal(
            service_key=api_key,
            authorization="",            # <-- or paste here if needed
            keyword="코로나",              # example keyword
            page=1,
            size=5,
            data_types=["FILE"],
        )
        print_search_results(data, max_items=5)

    except requests.HTTPError as e:
        print("HTTP error:", e)
        if e.response is not None:
            print("Response text:", e.response.text[:2000])

    except requests.RequestException as e:
        print("Request failed:", e)
