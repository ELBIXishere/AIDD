"""
WFS에서 전압 관련 필드/값을 조회하여 한글 보고서로 출력합니다.
- 전주/전선/변압기 레이어별 전압 관련 속성 수집
"""

import asyncio
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.wfs_client import WFSClient
from app.config import settings


# 전압 관련 키워드 (필드명 검색용)
VOLTAGE_KEYWORDS = ["VOLT", "VAL", "NOM", "POT", "VLT", "KND", "PHAR", "전압", "PRWR", "POLE_FORM", "POLE_KND"]

# 전형적인 전압값 (V)
TYPICAL_VOLTAGE_VALUES = ["22900", "13200", "6600", "380", "220", "110"]


def collect_voltage_fields(props: dict, layer_name: str) -> dict:
    """속성에서 전압 관련 필드만 추출"""
    out = {}
    for key, val in props.items():
        key_upper = (key or "").upper()
        if any(kw in key_upper for kw in VOLTAGE_KEYWORDS):
            if val is not None and str(val).strip() not in ("", "None"):
                out[key] = val
        # 값이 전형적인 전압 숫자면 필드명과 무관하게 수집
        if val is not None and str(val).strip() in TYPICAL_VOLTAGE_VALUES:
            out[key] = val
    return out


async def run_voltage_report():
    """WFS를 조회해 전압 관련 정보 보고서 생성"""
    client = WFSClient()
    # 설정에 정의된 BBox 또는 충주 지역 기본 박스
    bbox = (14240000, 4430000, 14250000, 4440000)
    max_feat = 2000

    print("=" * 80)
    print("전압 관련 정보 조회 보고서 (WFS)")
    print("=" * 80)
    print(f"WFS URL: {settings.GIS_WFS_URL}")
    print(f"레이어: 전주({settings.LAYER_POLE}), 전선({settings.LAYER_LINE}), 변압기/인입선({settings.LAYER_TRANSFORMER})")
    print(f"조회 영역 BBox: {bbox}, max_features={max_feat}")
    print()

    try:
        all_data = await client.get_facilities_by_bbox(
            bbox[0], bbox[1], bbox[2], bbox[3], max_features=max_feat
        )
    except Exception as e:
        print(f"[오류] WFS 조회 실패: {e}")
        print("네트워크 또는 WFS 서버(192.168.0.71) 연결을 확인하세요.")
        return

    # ---- 1. 전주 (Pole) 레이어 ----
    poles = all_data.get("poles", [])
    print("-" * 80)
    print("1. 전주 레이어 (AI_FAC_001.GIS_LOC) — 전압/형태 관련 필드")
    print("-" * 80)

    pole_volt_fields = {}   # 필드명 -> { 값 -> 건수 }
    pole_samples = []      # 샘플 행 (GID, POLE_FORM_CD, POLE_KND_CD 등)

    for p in poles:
        props = p.get("properties", {})
        vf = collect_voltage_fields(props, "pole")
        for f, v in vf.items():
            if f not in pole_volt_fields:
                pole_volt_fields[f] = {}
            vstr = str(v).strip()
            pole_volt_fields[f][vstr] = pole_volt_fields[f].get(vstr, 0) + 1
        # 전주 형태/종류 샘플
        pole_samples.append({
            "GID": props.get("GID"),
            "POLE_FORM_CD": props.get("POLE_FORM_CD"),
            "POLE_KND_CD": props.get("POLE_KND_CD"),
            "FAC_STAT_CD": props.get("FAC_STAT_CD"),
        })

    if pole_volt_fields:
        print("  [전압·형태 관련 필드 분포]")
        for f in sorted(pole_volt_fields.keys()):
            dist = pole_volt_fields[f]
            total = sum(dist.values())
            top = sorted(dist.items(), key=lambda x: -x[1])[:5]
            print(f"    • {f}: 총 {total}건 — 상위값: {top}")
    else:
        print("  (전압 관련 필드로 판단된 속성 없음)")

    print("  [샘플 속성 — GID, POLE_FORM_CD, POLE_KND_CD] (최대 10건)")
    for s in pole_samples[:10]:
        print(f"    GID={s['GID']}, POLE_FORM_CD={s['POLE_FORM_CD']}, POLE_KND_CD={s['POLE_KND_CD']}")
    print(f"  전주 피처 수: {len(poles)}")
    print()

    # ---- 2. 전선 (Line) 레이어 ----
    lines = all_data.get("lines", [])
    print("-" * 80)
    print("2. 전선 레이어 (AI_FAC_002.GIS_PTH) — 전압/종류/상 관련 필드")
    print("-" * 80)

    line_volt_fields = {}
    line_volt_val_dist = {}
    line_prwr_dist = {}
    line_phar_dist = {}

    for ln in lines:
        props = ln.get("properties", {})
        vf = collect_voltage_fields(props, "line")
        for f, v in vf.items():
            if f not in line_volt_fields:
                line_volt_fields[f] = {}
            vstr = str(v).strip()
            line_volt_fields[f][vstr] = line_volt_fields[f].get(vstr, 0) + 1

        v = props.get("VOLT_VAL")
        if v is not None:
            vs = str(v).strip()
            line_volt_val_dist[vs] = line_volt_val_dist.get(vs, 0) + 1
        k = props.get("PRWR_KND_CD")
        if k is not None:
            ks = str(k).strip()
            line_prwr_dist[ks] = line_prwr_dist.get(ks, 0) + 1
        ph = props.get("PHAR_CLCD")
        if ph is not None:
            phs = str(ph).strip()
            line_phar_dist[phs] = line_phar_dist.get(phs, 0) + 1

    print("  [VOLT_VAL(전압값) 분포]")
    if line_volt_val_dist:
        for v, cnt in sorted(line_volt_val_dist.items(), key=lambda x: -x[1]):
            print(f"    {v or '(빈값)'}: {cnt}건")
    else:
        print("    (값 없음 — 전선은 PRWR_KND_CD 등으로 고압/저압 구분)")
    print("  [PRWR_KND_CD(전선 종류) 분포]")
    for k, cnt in sorted(line_prwr_dist.items(), key=lambda x: -x[1])[:15]:
        print(f"    {k or '(빈값)'}: {cnt}건")
    print("  [PHAR_CLCD(상 구분) 분포]")
    for ph, cnt in sorted(line_phar_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"    {ph or '(빈값)'}: {cnt}건")
    if line_volt_fields:
        print("  [기타 전압 관련 필드]")
        for f in sorted(line_volt_fields.keys()):
            if f in ("VOLT_VAL", "PRWR_KND_CD", "PHAR_CLCD"):
                continue
            dist = line_volt_fields[f]
            print(f"    • {f}: {dict(sorted(dist.items(), key=lambda x: -x[1])[:3])}")
    print(f"  전선 피처 수: {len(lines)}")
    print()

    # ---- 3. 변압기/인입선 레이어 ----
    transformers = all_data.get("transformers", [])
    print("-" * 80)
    print("3. 변압기/인입선 레이어 (AI_FAC_003.GIS_PTH) — 전압 관련 필드")
    print("-" * 80)

    tr_volt_fields = {}
    for t in transformers:
        props = t.get("properties", {})
        vf = collect_voltage_fields(props, "transformer")
        for f, v in vf.items():
            if f not in tr_volt_fields:
                tr_volt_fields[f] = {}
            vstr = str(v).strip()
            tr_volt_fields[f][vstr] = tr_volt_fields[f].get(vstr, 0) + 1

    if tr_volt_fields:
        print("  [전압 관련 필드 분포]")
        for f in sorted(tr_volt_fields.keys()):
            dist = tr_volt_fields[f]
            top = sorted(dist.items(), key=lambda x: -x[1])[:5]
            print(f"    • {f}: {top}")
    else:
        print("  (전압 관련 필드로 판단된 속성 없음)")
    print(f"  변압기/인입선 피처 수: {len(transformers)}")
    print()

    # ---- 요약 ----
    print("=" * 80)
    print("요약 — 애플리케이션에서 사용하는 전압 관련 필드")
    print("=" * 80)
    print("""
  • 전주: POLE_FORM_CD (H=고압, L=저압, G=지지주), POLE_KND_CD
  • 전선: VOLT_VAL(전압값, 22900/380/220 등), PRWR_KND_CD(종류→고압/저압), PHAR_CLCD(상)
  • 고압/저압 판단: VOLT_VAL>=1000 → 고압, PRWR_KND_CD HV/EW 등 → 고압, 그 외 → 저압
""")


if __name__ == "__main__":
    async def _main():
        try:
            await run_voltage_report()
        finally:
            await WFSClient.close_pool()
    asyncio.run(_main())
