import requests
import json
from datetime import datetime

SERVICE_KEY = "a74283c86795400b9c0a726ab71ff877ca82a779423e932ca9eee342778dc73d"

# 문서상 요청주소 (https 로 바꿈)
BASE_URL = "https://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList"

# 선호 종관 지점: 서울(108)
DEFAULT_STN_ID = "108"


def fetch_asos_range(start_dt, start_hh, end_dt, end_hh, stn_id=DEFAULT_STN_ID):
    """
    ASOS 시간자료를 특정 시간 구간에 대해 조회해서 item 리스트를 반환
    start_dt, end_dt: datetime.date 또는 datetime 객체
    start_hh, end_hh: 정수 (0~23)
    """

    if not SERVICE_KEY or SERVICE_KEY.strip() == "":
        raise SystemExit("SERVICE_KEY가 비어 있음. data.go.kr 인증키를 넣어야 합니다.")

    # 공공데이터포털 가이드:
    # - Query 방식:  key = serviceKey (소문자 s)
    # - Header 방식: Authorization: Infuser {API_KEY}
    params = {
        "serviceKey": SERVICE_KEY,  # ← 가이드에 나온 이름 그대로
        "dataType": "JSON",
        "dataCd": "ASOS",
        "dateCd": "HR",
        "startDt": start_dt.strftime("%Y%m%d"),
        "startHh": f"{start_hh:02d}",
        "endDt": end_dt.strftime("%Y%m%d"),
        "endHh": f"{end_hh:02d}",
        "stnIds": stn_id,
        "pageNo": 1,
        "numOfRows": 999,
    }

    headers = {
        # swagger 가이드에 있는 형식
        # Header Key: Authorization, Value: Infuser {API_KEY}
        "Authorization": "Infuser " + SERVICE_KEY
    }

    print(
        f"[요청] {params['startDt']} {params['startHh']}시 ~ "
        f"{params['endDt']} {params['endHh']}시, stnId={stn_id}"
    )

    resp = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
    print(f"  -> 요청 URL: {resp.url}")

    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print("[HTTP 오류 발생]")
        print(f"상태 코드: {resp.status_code}")
        try:
            print("응답 본문 일부:")
            print(resp.text[:500])
        except Exception:
            pass
        raise SystemExit(e)

    # 여기까지 왔다는 건 HTTP 200은 성공했다는 뜻
    data = resp.json()

    response = data.get("response", {})
    header = response.get("header", {})
    body = response.get("body", {})

    result_code = header.get("resultCode")
    result_msg = header.get("resultMsg")

    # API 내부 에러코드 체크 (여기서부터는 HTTP 200이어도 오류일 수 있음)
    if result_code != "00":
        raise SystemExit(f"API 오류: {result_code} {result_msg}")

    items = body.get("items")
    if not items:
        print("  -> 조회 결과 없음 (items가 비어 있음)")
        return []

    item_list = items.get("item", [])
    if isinstance(item_list, dict):
        item_list = [item_list]

    print(f"  -> {len(item_list)}건 조회됨")
    return item_list


def save_json(items, filename):
    """조회 결과 리스트를 JSON 파일로 저장"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"[저장 완료] {filename} ({len(items)}건)")


def main():
    # 1) 2024-12-04 15시 ~ 18시
    dt1 = datetime(2024, 12, 4)
    items1 = fetch_asos_range(dt1, 15, dt1, 18)
    save_json(items1, "asos_20241204_15_18_seoul_108.json")

    # 2) 2025-06-04 12시 ~ 16시
    dt2 = datetime(2025, 6, 4)
    items2 = fetch_asos_range(dt2, 12, dt2, 16)
    save_json(items2, "asos_20250604_12_16_seoul_108.json")

    # 3) 숙제 제출일(2025-11-20) 기준 이틀 전: 2025-11-18 00시 ~ 03시
    dt3 = datetime(2025, 11, 18)
    items3 = fetch_asos_range(dt3, 0, dt3, 3)
    save_json(items3, "asos_20251118_00_03_seoul_108.json")


if __name__ == "__main__":
    main()
