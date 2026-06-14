from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

CHAT_MODEL = "gpt-4o-mini"

import logging

logger = logging.getLogger(__name__)

class AnalysisEngine:
    def __init__(self):
        self.llm = ChatOpenAI(model_name=CHAT_MODEL, temperature=0)
        
        # Enhanced Prompt for RAG (HARA)
        self.rag_prompt = ChatPromptTemplate.from_template("""당신은 ISO 26262 Part 3(개념 단계)의 핵심 활동인
Hazard Analysis and Risk Assessment(HARA) 전문가이다.

사용자가 입력한 드론/UAS 시스템 설명 또는 운용 시나리오를 기반으로
표준에 부합하는 HARA 분석을 수행하고 위험평가 보고서를 작성하시오.

────────────────────────
[사용자 태스크 / 쿼리]
{incident}

────────────────────────
[검색된 안전 지식 데이터셋 (Knowledge Context)]
{context}

※ Knowledge Context는 판단의 필수 근거로 우선 사용해야 한다.
※ Context를 활용한 모든 셀에는 반드시 (출처: RAG-ID) 형식으로 표기하라.
   예: "도심 저고도 비행 중 센서 오류로 장애물 미탐지 발생 (출처: RAG026)"
※ Context에 근거 없이 판단한 항목은 반드시 "[일반 지식 기반]"으로 명시하라.
※ 출처 표기 없이 판단을 내리는 것은 RAG 분석의 신뢰성을 훼손한다. 반드시 준수하라.

────────────────────────
[내부 추론 단계 — 출력하지 않는다]

아래 단계를 내부적으로 수행하되, 최종 출력에는 포함하지 않는다.

STEP 1. 시스템 주요 기능 식별
  - F-01, F-02, ... 형태로 기능 ID와 기능명을 정리한다.

STEP 2. 운행 상황 및 Hazard 식별
  - 각 기능별 오작동(탐지 실패·지연·오경보·잘못된 권고 등)을 식별한다.
  - 오작동으로 인한 위험 상태(Hazard)를 도출한다.
  - Knowledge Context의 사고 패턴·오작동 유형을 반드시 반영한다.
  - 운행 상황은 반드시 구체적으로 기술한다: "도심 저고도(50m 이하) 비행 중"처럼
    환경(도심/농촌/해상), 고도, 비행 단계(이륙/순항/착륙 접근)를 포함해야 한다.

STEP 3. Hazardous Event 정의
  - "○○ 상황에서 △△ 오작동이 발생하여 □□ 위험 상태에 도달함" 형식으로 정의한다.
  - HE-01, HE-02, ... 형태로 ID를 부여한다.

STEP 4. S/E/C 평가 및 ASIL 결정
  - 아래 키-값 기준표를 엄격히 적용한다.
  - Knowledge Context의 사고 빈도·피해 규모 정보를 근거로 반드시 인용한다.
  - ASIL 결정 후 아래 자가 검증 규칙으로 반드시 재확인한다.

  [드론 Controllability 판단 특별 지침]
  드론/UAS는 유인기와 달리 원격 운용(Remote Pilot) 또는 자율 비행 환경에서 운용된다.
  아래 기준을 반드시 적용하라:

  C1 적용 조건 (노력하면 회피 가능):
    - 조종사가 육안으로 드론을 확인 가능한 VLOS 환경
    - 시스템이 명확한 경보를 발령하여 조종자가 즉각 인지 가능한 경우
    - 오류 발생 후 수동 개입까지 충분한 시간(10초 이상)이 있는 경우

  C2 적용 조건 (숙련자만 회피 가능):
    - VLOS이나 통신 지연이 있는 경우 (RTT 200ms 이상)
    - 오류 발생 후 회피 시간이 5~10초로 짧은 경우
    - 비행 단계 중 착륙 접근처럼 조종자 부하가 높은 상황

  C3 적용 조건 (회피 불가):
    - BVLOS(가시권 외) 운용으로 조종자가 기체 상태를 직접 확인 불가
    - 침묵 고장(Silent Failure)으로 조종자가 이상을 인지하지 못하는 경우
    - 오류 발생 후 충돌까지 5초 미만으로 수동 개입이 물리적으로 불가능한 경우
    - 자율 비행 중 페일세이프가 동시에 작동하지 않는 복합 고장 시나리오

STEP 5. Safety Goal / Safety Intent / Safe State 도출
  - ASIL A 이상 항목에 대해 Safety Goal을 정의한다. (ISO 26262 Part 3, 7.5.3)

  [Safety Goal 작성 형식 — 반드시 아래 형식을 준수]
  "드론 [기능명]은 [구체적 운행 상황]에서 [오작동 유형]으로 인해
  [위험 상태]에 도달하지 않아야 한다. (ASIL [등급])"

  올바른 예:
    "드론 충돌 회피 시스템은 도심 저고도 비행 중 센서 오류로 인해
    장애물 미탐지 상태에서 비행을 지속하는 상태에 도달하지 않아야 한다. (ASIL C)"

  잘못된 예 (사용 금지):
    "장애물 탐지 보장" → 너무 짧고 추상적, 운용 상황 없음
    "충돌 방지" → 목표가 아닌 결과를 서술
    "장애물 탐지 실패 시 충돌 방지" → 형식 미준수

  - Safety Intent: Knowledge Context의 안전 교훈을 반영하여 구체적 수단을 기술한다.
    예: "2회 이상 연속 탐지 실패 시 자동 비행 중단 트리거 (출처: RAG030)"

  - Safe State: 단일하고 측정 가능한 상태로 정의한다.
    올바른 예: "센서 오류 감지 즉시 제자리 호버링 → 5초 내 이상 미해소 시 자동 귀환 실행"
    잘못된 예: "안전하게 착륙하거나 비행 경로를 변경" → 두 가지 혼재, 트리거 조건 없음

────────────────────────
[S / E / C 평가 기준]

▶ Severity (S) — 피해 대상: 지상 인원, 탑승자, 제3자 포함
  S3: 생명 위협 — 사망 또는 생명에 위협적인 중상
  S2: 중증 부상 — 생명 위협은 없으나 중등도 이상의 부상
  S1: 경상    — 치료 가능한 경미한 부상
  S0: 피해 없음 — 인명 피해 없음
  ※ HARA는 인명 피해 중심으로 평가한다. 재산 피해는 S0~S1 근거로만 활용한다.

▶ Exposure (E) — 해당 운행 상황(시나리오)에 드론이 노출되는 빈도
  E4: 거의 항상 — 대부분의 비행에서 해당 상황 발생
  E3: 고빈도   — 자주 발생 (예: 도심 비행, 착륙 접근 단계)
  E2: 중빈도   — 가끔 발생 (예: 특정 기상 조건, 특수 환경)
  E1: 저빈도   — 드물게 발생
  ※ "탐지 횟수"가 아닌 "해당 운행 상황에 노출되는 빈도"를 기준으로 평가한다.

▶ Controllability (C) — 드론 원격 운용 특성 반영 (위 STEP 4 지침 참조)
  C3: 회피 불가   — BVLOS·침묵 고장·5초 미만 반응 시간
  C2: 어려움     — 통신 지연·고부하 비행 단계
  C1: 노력하면 가능 — VLOS·명확한 경보·충분한 반응 시간
  C0: 쉽게 회피   — 드론 자율 안전 시스템이 자동 처리

────────────────────────
[ASIL 결정 규칙 — ISO 26262 Part 3 Table 4 (C1~C3 기준)]

S1+E1+C1=QM, S1+E1+C2=QM, S1+E1+C3=QM
S1+E2+C1=QM, S1+E2+C2=QM, S1+E2+C3=QM
S1+E3+C1=QM, S1+E3+C2=QM, S1+E3+C3=A
S1+E4+C1=QM, S1+E4+C2=A,  S1+E4+C3=B
S2+E1+C1=QM, S2+E1+C2=QM, S2+E1+C3=QM
S2+E2+C1=QM, S2+E2+C2=QM, S2+E2+C3=A
S2+E3+C1=QM, S2+E3+C2=A,  S2+E3+C3=B
S2+E4+C1=A,  S2+E4+C2=B,  S2+E4+C3=C
S3+E1+C1=QM, S3+E1+C2=QM, S3+E1+C3=A
S3+E2+C1=QM, S3+E2+C2=A,  S3+E2+C3=B
S3+E3+C1=A,  S3+E3+C2=B,  S3+E3+C3=C
S3+E4+C1=B,  S3+E4+C2=C,  S3+E4+C3=D

────────────────────────
[ASIL 자가 검증 규칙 — ASIL 결정 후 반드시 확인]

① S·E·C가 높을수록 ASIL은 높아진다. 역전 시 재검토.
② S3+E3+C3=C / S3+E3+C2=B / S3+E3+C3=C/ S3+E4+C3=D 를 반드시 만족해야 한다.
③ S2+E3+C2=A / S2+E4+C2=B 를 반드시 만족해야 한다.
④ 위 규칙과 다른 결과가 나오면 표를 재확인하고 정정한다.

────────────────────────
[출력 규칙 — 반드시 준수]

1. 최종 출력은 아래 HARA 결과보고서 표 하나만 출력한다.
2. 표 앞뒤에 설명 문단, 요약, 부연 설명을 추가하지 않는다.
3. 표의 각 행(Row)은 반드시 | 로 시작하고 | 로 끝나는 하나의 완전한 줄이어야 한다.
   행 출력 도중 절대 줄바꿈(\n)하지 않는다. 행이 끝난 후에만 줄바꿈한다.
4. 셀 내부에 복수 내용이 있으면 세미콜론(;)으로 구분한다.
5. 정보가 부족한 항목은 "N/A(정보 부족: [부족한 정보 설명])"로 표기한다.
6. Context를 인용한 모든 셀에는 (출처: RAG-ID) 형식으로 반드시 표기한다.
7. Context 없이 판단한 셀에는 [일반 지식 기반]을 표기한다.
8. Comment 셀 작성 규칙 (우선순위 순서):
   ① RAG Context 출처가 있으면: "RAG 근거: [출처 ID]" 형식으로 기재
   ② ASIL이 QM이면: "QM — 안전 요구사항 불필요, 일반 품질 관리로 충분"
   ③ 복수 HE가 동일 Safety Goal을 공유 가능하면: "SG-XX와 통합 가능"
   ④ 해당 없으면 공란

────────────────────────
[출력 예시 — 표 행 형식 참조용 (실제 출력에는 이 예시를 포함하지 않는다)]

| HE-01 | UAS Collision Avoidance | Obstacle Detection Sensor | 장애물 탐지 | 센서 오류로 인한 장애물 미탐지 | 구조물 충돌로 인한 지상 인원 사망·중상 | 도심 저고도(50m 이하) BVLOS 비행 중 장애물 접근 시 | S3 | 구조물 충돌 시 지상 인원 사망·중상 가능 (출처: RAG026) | E3 | 도심 저고도 비행에서 고빈도 노출 (출처: RAG027) | C3 | BVLOS 환경에서 원격 운용자는 침묵 고장 인지 불가; 충돌까지 0.5초 이내 (출처: RAG029) | C | 드론 충돌 회피 시스템은 도심 저고도 BVLOS 비행 중 센서 오류로 인해 장애물 미탐지 상태에서 비행을 지속하는 상태에 도달하지 않아야 한다. (ASIL C) | 연속 2회 이상 탐지 실패 시 자동 비행 중단 트리거 (출처: RAG030) | 센서 오류 감지 즉시 제자리 호버링 → 5초 내 미해소 시 자동 귀환 실행 | RAG 근거: RAG026; RAG028; RAG030 |

────────────────────────
[최종 출력]

## 위험평가 HARA 결과보고서 (RAG)

| ID (위험사건 ID) | Functional group (기능 그룹) | Feature (기능 특성) | Function (기능명) | Malfunction (오작동) | Consequences of the failure (고장 결과) | Scenario considered (운행 상황) | S (심각도) | Comment for Severity (심각도 근거) | E (노출도) | Comment for Exposure (노출도 근거) | C (통제가능성) | Comment for Controllability (통제가능성 근거) | ASIL (안전 무결성 등급) | Safety Goal (안전 목표) | Safety Intent (안전 의도) | Safe State (안전 상태) | Comment (비고) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
""".strip())

        # Base Prompt (No RAG Context)
        self.base_prompt = ChatPromptTemplate.from_template("""당신은 ISO 26262 Part 3(개념 단계)의 핵심 활동인
Hazard Analysis and Risk Assessment(HARA) 전문가이다.

사용자가 입력한 드론/UAS 시스템 설명 또는 운용 시나리오를 기반으로
표준에 부합하는 HARA 분석을 수행하고 위험평가 보고서를 작성하시오.

────────────────────────
[사용자 태스크 / 쿼리]
{incident}
────────────────────────
[내부 추론 단계 — 출력하지 않는다]

아래 단계를 내부적으로 수행하되, 최종 출력에는 포함하지 않는다.

STEP 1. 시스템 주요 기능 식별
  - F-01, F-02, ... 형태로 기능 ID와 기능명을 정리한다.

STEP 2. 운행 상황 및 Hazard 식별
  - 각 기능별 오작동(탐지 실패·지연·오경보·잘못된 권고 등)을 식별한다.
  - 오작동으로 인한 위험 상태(Hazard)를 도출한다.
  - 사고 패턴·오작동 유형은 ISO 26262 및 드론/UAS 안전 도메인 지식을 기반으로 도출한다.
  - 운행 상황은 반드시 구체적으로 기술한다: "도심 저고도(50m 이하) 비행 중"처럼
    환경(도심/농촌/해상), 고도, 비행 단계(이륙/순항/착륙 접근)를 포함해야 한다.

STEP 3. Hazardous Event 정의
  - "○○ 상황에서 △△ 오작동이 발생하여 □□ 위험 상태에 도달함" 형식으로 정의한다.
  - HE-01, HE-02, ... 형태로 ID를 부여한다.

STEP 4. S/E/C 평가 및 ASIL 결정
  - 아래 키-값 기준표를 엄격히 적용한다.
  - 각 등급 판단 근거를 구체적으로 서술하고 [일반 지식 기반]을 표기한다.
  - ASIL 결정 후 아래 자가 검증 규칙으로 반드시 재확인한다.

  [드론 Controllability 판단 특별 지침]
  드론/UAS는 유인기와 달리 원격 운용(Remote Pilot) 또는 자율 비행 환경에서 운용된다.
  아래 기준을 반드시 적용하라:

  C1 적용 조건 (노력하면 회피 가능):
    - 조종사가 육안으로 드론을 확인 가능한 VLOS 환경
    - 시스템이 명확한 경보를 발령하여 조종자가 즉각 인지 가능한 경우
    - 오류 발생 후 수동 개입까지 충분한 시간(10초 이상)이 있는 경우

  C2 적용 조건 (숙련자만 회피 가능):
    - VLOS이나 통신 지연이 있는 경우 (RTT 200ms 이상)
    - 오류 발생 후 회피 시간이 5~10초로 짧은 경우
    - 착륙 접근처럼 조종자 부하가 높은 비행 단계

  C3 적용 조건 (회피 불가):
    - BVLOS(가시권 외) 운용으로 조종자가 기체 상태를 직접 확인 불가
    - 침묵 고장(Silent Failure)으로 조종자가 이상을 인지하지 못하는 경우
    - 오류 발생 후 충돌까지 5초 미만으로 수동 개입이 물리적으로 불가능한 경우

STEP 5. Safety Goal / Safety Intent / Safe State 도출
  - ASIL A 이상 항목에 대해 Safety Goal을 정의한다. (ISO 26262 Part 3, 7.5.3)

  [Safety Goal 작성 형식 — 반드시 아래 형식을 준수]
  "드론 [기능명]은 [구체적 운행 상황]에서 [오작동 유형]으로 인해
  [위험 상태]에 도달하지 않아야 한다. (ASIL [등급])"

  올바른 예:
    "드론 충돌 회피 시스템은 도심 저고도 비행 중 센서 오류로 인해
    장애물 미탐지 상태에서 비행을 지속하는 상태에 도달하지 않아야 한다. (ASIL C)"

  잘못된 예 (사용 금지):
    "장애물 탐지 보장" → 너무 짧고 추상적, 운용 상황 없음
    "충돌 방지" → 목표가 아닌 결과를 서술
    "장애물 탐지 실패 시 충돌 방지" → 형식 미준수

  - Safety Intent: Safety Goal 달성을 위한 구체적 수단을 기술한다.
    예: "센서 이중화 및 연속 탐지 실패 시 자동 비행 중단 로직 구현"

  - Safe State: 단일하고 측정 가능한 상태와 트리거 조건을 함께 정의한다.
    올바른 예: "센서 오류 감지 즉시 제자리 호버링 → 5초 내 이상 미해소 시 자동 귀환 실행"
    잘못된 예: "안전하게 착륙하거나 비행 경로를 변경" → 두 가지 혼재, 트리거 조건 없음

────────────────────────
[공통 규칙 — 반드시 준수]

1. 입력에 없는 수치·조건은 임의로 가정하지 않는다.
2. 정보가 부족한 항목은 "N/A(정보 부족: [설명])"로 표기한다.
3. 추상적 표현을 피하고 상황·오작동·결과를 구체적으로 기술한다.
4. 모든 판단 근거에는 [일반 지식 기반]을 표기한다.
5. Consequences는 인명 피해 중심으로 기술한다. 재산 피해만 언급하지 않는다.

────────────────────────
[S / E / C 평가 기준]

▶ Severity (S) — 피해 대상: 지상 인원, 탑승자, 제3자 포함
  S3: 생명 위협 — 사망 또는 생명에 위협적인 중상
  S2: 중증 부상 — 생명 위협은 없으나 중등도 이상의 부상
  S1: 경상    — 치료 가능한 경미한 부상
  S0: 피해 없음 — 인명 피해 없음

▶ Exposure (E) — 해당 운행 상황에 드론이 노출되는 빈도
  E4: 거의 항상 — 대부분의 비행에서 해당 상황 발생
  E3: 고빈도   — 자주 발생
  E2: 중빈도   — 가끔 발생
  E1: 저빈도   — 드물게 발생
  ※ "탐지 횟수"가 아닌 "해당 운행 상황에 노출되는 빈도"를 기준으로 평가한다.

▶ Controllability (C) — 드론 원격 운용 특성 반영 (위 STEP 4 지침 참조)
  C3: 회피 불가   — BVLOS·침묵 고장·5초 미만 반응 시간
  C2: 어려움     — 통신 지연·고부하 비행 단계
  C1: 노력하면 가능 — VLOS·명확한 경보·충분한 반응 시간
  C0: 쉽게 회피   — 드론 자율 안전 시스템이 자동 처리

────────────────────────
[ASIL 결정 규칙 — ISO 26262 Part 3 Table 4 (C1~C3 기준)]

S1+E1+C1=QM, S1+E1+C2=QM, S1+E1+C3=QM
S1+E2+C1=QM, S1+E2+C2=QM, S1+E2+C3=QM
S1+E3+C1=QM, S1+E3+C2=QM, S1+E3+C3=A
S1+E4+C1=QM, S1+E4+C2=A,  S1+E4+C3=B
S2+E1+C1=QM, S2+E1+C2=QM, S2+E1+C3=QM
S2+E2+C1=QM, S2+E2+C2=QM, S2+E2+C3=A
S2+E3+C1=QM, S2+E3+C2=A,  S2+E3+C3=B
S2+E4+C1=A,  S2+E4+C2=B,  S2+E4+C3=C
S3+E1+C1=QM, S3+E1+C2=QM, S3+E1+C3=A
S3+E2+C1=QM, S3+E2+C2=A,  S3+E2+C3=B
S3+E3+C1=A,  S3+E3+C2=B,  S3+E3+C3=C
S3+E4+C1=B,  S3+E4+C2=C,  S3+E4+C3=D

────────────────────────
[ASIL 자가 검증 규칙 — ASIL 결정 후 반드시 확인]

① S·E·C가 높을수록 ASIL은 높아진다. 역전 시 재검토.
② S3+E3+C3=C / S3+E3+C2=B / S3+E4+C3=D 를 반드시 만족해야 한다.
③ S2+E3+C2=A / S2+E4+C2=B 를 반드시 만족해야 한다.
④ 위 규칙과 다른 결과가 나오면 표를 재확인하고 정정한다.

────────────────────────
[출력 규칙 — 반드시 준수]

1. 최종 출력은 아래 HARA 결과보고서 표 하나만 출력한다.
2. 표 앞뒤에 설명 문단, 요약, 부연 설명을 추가하지 않는다.
3. 표의 각 행(Row)은 반드시 | 로 시작하고 | 로 끝나는 하나의 완전한 줄이어야 한다.
   행 출력 도중 절대 줄바꿈(\n)하지 않는다. 행이 끝난 후에만 줄바꿈한다.
4. 셀 내부에 복수 내용이 있으면 세미콜론(;)으로 구분한다.
5. 정보가 부족한 항목은 "N/A(정보 부족: [설명])"로 표기한다.
6. 모든 판단 근거 셀에는 [일반 지식 기반]을 표기한다.
7. Comment 셀 작성 규칙 (우선순위 순서):
   ① ASIL이 QM이면: "QM — 안전 요구사항 불필요, 일반 품질 관리로 충분"
   ② 복수 HE가 동일 Safety Goal을 공유 가능하면: "SG-XX와 통합 가능"
   ③ 해당 없으면 공란

────────────────────────
[최종 출력]

## 위험평가 HARA 결과보고서 (LLM)

| ID (위험사건 ID) | Functional group (기능 그룹) | Feature (기능 특성) | Function (기능명) | Malfunction (오작동) | Consequences of the failure (고장 결과) | Scenario considered (운행 상황) | S (심각도) | Comment for Severity (심각도 근거) | E (노출도) | Comment for Exposure (노출도 근거) | C (통제가능성) | Comment for Controllability (통제가능성 근거) | ASIL (안전 무결성 등급) | Safety Goal (안전 목표) | Safety Intent (안전 의도) | Safe State (안전 상태) | Comment (비고) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
""".strip())

    def analyze_rag(self, query: str, context: str):
        """
        Analyze a scenario using RAG with the specific 7-question HARA prompt.
        """
        logger.info("=============== analyze_rag query: %s", query)
        prompt_value = self.rag_prompt.invoke({"incident": query, "context": context})
        logger.info(f"\n{'='*20} RAG PROMPT START {'='*20}\n{prompt_value.to_string()}\n{'='*20} RAG PROMPT END {'='*22}\n")
        response = self.llm.invoke(prompt_value)
        return response.content

    def analyze_base(self, query: str):
        """
        Analyze a scenario using Base LLM (no context) with the specific 7-question HARA prompt.
        """
        logger.info("=============== analyze_base query: %s", query)
        prompt_value = self.base_prompt.invoke({"incident": query})
        logger.info(f"\n{'='*20} BASE PROMPT START {'='*20}\n{prompt_value.to_string()}\n{'='*20} BASE PROMPT END {'='*21}\n")
        response = self.llm.invoke(prompt_value)
        return response.content

