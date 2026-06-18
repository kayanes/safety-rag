# RAG 기반 LLM을 활용한 항공 시스템 안전 분석 자동화: SFHA와 HARA 비교 연구

> Automation of Aviation System Safety Analysis Using a RAG-Based LLM: A Comparative Study of SFHA and HARA

본 저장소는 위 연구의 재현을 위한 코드, 프롬프트, 평가 플랫폼 코드를 제공합니다.

---

## 개요 (Overview)

항공 시스템의 안전 분석은 방대한 데이터와 문서 검토를 요구하는 전문가 집약적 작업입니다. 본 연구는 FAA AIDS(Accident/Incident Data System) 사고·고장 데이터를 기반으로 안전 지식 데이터셋을 구축하고, GPT-4o-mini와 RAG(Retrieval-Augmented Generation)를 결합한 파이프라인을 구현하여 안전 분석 리포트 생성을 자동화합니다.

두 가지 표준 안전 분석 방법론인 **SFHA**(System Functional Hazard Assessment, ARP 4761A)와 **HARA**(Hazard Analysis and Risk Assessment, ISO 26262)를 각각 LLM 단독 조건과 RAG 조건에서 수행하고, 12인 전문가의 블라인드 평가로 비교했습니다.

### 연구 질문 (Research Questions)

- **RQ1.** 항공 시스템의 자동화 안전 분석을 RAG 기반 생성형 AI로 수행할 때, 위험분석평가 리포트가 효과적으로 생성되는가?
- **RQ2.** RAG 기반 안전 분석 환경에서 SFHA와 HARA 중 어떤 기법이 더 적합한 결과를 제공하는가?

### 주요 결과 (Key Findings)

| 조건 | LLM 단독 | RAG | 향상폭 |
|------|---------|-----|--------|
| HARA | 64.7 | 76.2 | +11.5 |
| SFHA | 70.7 | 79.2 | +8.5 |

- RAG 조건에서 두 방법론 모두 실무 활용 가능 수준(60점)을 일관되게 상회 (RQ1)
- SFHA가 5개 시나리오 전체에서 우위, 12인 중 7인이 SFHA 선호 (RQ2)

*점수는 100점 만점 정규화 기준이며, 본 연구는 탐색적 개념 증명(Proof of Concept) 수준의 결과입니다.*

---

## 저장소 구조 (Repository Structure)

현재 프로젝트는 **백엔드(FastAPI)**와 **프론트엔드(Next.js)**가 분리된 모노레포 구조로 되어 있습니다. 실험에 사용된 프롬프트와 RAG 파이프라인은 백엔드 소스코드 내에 포함되어 있습니다.

```text
.
├── hara-legacy-rag/            # 백엔드: RAG 파이프라인 및 LLM 분석 서버 (FastAPI)
│   ├── app/
│   │   ├── services/           # SFHA/HARA 분석 엔진 및 프롬프트 정의, RAG 모듈
│   │   └── db/                 # 데이터베이스 모델 및 세션 (SQLite 사용)
│   ├── data/                   # 분석 및 지식 검색용 데이터 디렉터리
│   ├── main.py                 # FastAPI 서버 진입점
│   └── requirements.txt        # Python 의존성 목록
├── hara-rag-eval-platform/     # 프론트엔드: 실험 결과 시각화 및 평가 플랫폼 (Next.js)
│   ├── src/                    # React 페이지 컴포넌트 (실험 생성, 보고서 뷰어 등)
│   ├── public/                 # 정적 리소스
│   └── package.json            # Node.js 의존성 목록
├── README.md                   # 프로젝트 개요 (현재 파일)
└── .gitignore                  # Git 무시 파일 목록
```

---

## 설치 및 실행 (Installation & Usage)

### 1. 백엔드 설정 (RAG 및 LLM API 서버)

백엔드 서버는 `hara-legacy-rag` 폴더에서 실행됩니다.

```bash
cd hara-legacy-rag

# 가상 환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
# 폴더 내에 .env 파일을 생성하고 본인의 OpenAI API 키를 입력합니다.
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env

# 서버 실행
uvicorn main:app --reload --port 8000
```
- 서버가 실행되면 `http://127.0.0.1:8000/docs` 에서 API 문서를 확인할 수 있습니다.

### 2. 프론트엔드 설정 (평가 UI 플랫폼)

프론트엔드 서버는 `hara-rag-eval-platform` 폴더에서 실행됩니다. 백엔드가 실행 중인 상태에서 진행하세요.

```bash
cd ../hara-rag-eval-platform

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```
- 실행 후 브라우저에서 `http://localhost:3000` 에 접속하여 평가 플랫폼 UI를 사용할 수 있습니다.

---

## 실험 설정 (Experimental Setup)

| 항목 | 내용 |
|------|------|
| 생성 모델 | GPT-4o-mini |
| 벡터 데이터베이스 | ChromaDB |
| 지식 출처 | FAA AIDS (Accident/Incident Data System) |
| 시나리오 | 충돌 회피, 통신 링크, 배터리 방전, 모드 전환, 센서 불일치 (5개) |
| 평가자 | 12인 전문가 (블라인드 평가) |
| 평가 항목 | 7개 항목, 5점 리커트 척도 |

---

## 데이터 및 개인정보 (Data & Privacy)

- **평가 데이터:** 평가자 개인정보 보호를 위해 모든 점수는 익명 식별자(E1~E12)로만 관리됩니다.
- **FAA AIDS 데이터:** 미국 연방항공청(FAA)이 공개한 데이터로, 원본은 [asias.faa.gov](https://asias.faa.gov)에서 확인할 수 있습니다.

> **보안 주의:** 저장소를 공개하기 전에 `.env`(API 키)와 SQLite DB 파일에 평가자 실명·소속 등 개인정보나 비밀 키가 커밋되지 않았는지 반드시 확인하세요. `.gitignore`에 `.env`, `*.db`, `*.sqlite3` 등이 포함되어 있는지 점검을 권장합니다.


---

## 라이선스 (License)

- **코드:** [MIT License](LICENSE)
- **데이터:** 학술·연구 목적 사용 시 본 연구 인용을 요청합니다.

---

## 면책 (Disclaimer)

본 저장소의 코드와 결과는 연구 목적의 개념 증명(Proof of Concept)입니다. 생성형 AI가 자동 생성한 안전 분석 리포트는 전문가의 검토 없이 실제 안전 인증이나 운용 결정에 사용해서는 안 됩니다.
