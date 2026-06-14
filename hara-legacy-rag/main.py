from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict

from app.db.session import engine, get_db
from app.db.models import Base
from app.services.ingestion_service import sync_legacy_db_to_chroma
from app.services.rag_engine import RAGEngine
from app.services.analysis_engine import AnalysisEngine
from app.services.sfha_analysis_engine import SfhaAnalysisEngine
from dotenv import load_dotenv
import os
import json

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HARA Legacy RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_engine_instance      = None
analysis_engine_instance = None
sfha_analysis_engine_instance = None

def get_rag_engine():
    global rag_engine_instance
    if rag_engine_instance is None:
        rag_engine_instance = RAGEngine()
    return rag_engine_instance

def get_analysis_engine():
    global analysis_engine_instance
    if analysis_engine_instance is None:
        analysis_engine_instance = AnalysisEngine()
    return analysis_engine_instance

def get_sfha_analysis_engine():
    global sfha_analysis_engine_instance
    if sfha_analysis_engine_instance is None:
        sfha_analysis_engine_instance = SfhaAnalysisEngine()
    return sfha_analysis_engine_instance

class AnalyzeRequest(BaseModel):
    query:        str
    filters:      Optional[Dict[str, str]] = None
    mode:         Optional[str]            = "rag"   # "rag" or "base"
    experiment_type: Optional[str]         = "hara"  # "hara" or "sfha"
    ground_truth: Optional[str]            = None
    context:      Optional[str]            = None

@app.on_event("startup")
async def startup_event():
    pass

@app.get("/")
def read_root():
    return {"message": "HARA Legacy RAG Service is running."}

@app.post("/api/v1/sync")
def trigger_sync(db: Session = Depends(get_db)):
    """Legacy DB → Vector Store ETL 트리거"""
    try:
        result = sync_legacy_db_to_chroma(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 추가 imports ──────────────────────────────────────────────────────────────
from sqlalchemy import desc, or_, cast, Integer, func
from app.db.models import AnalysisResult
from app.services.parser_service import ParserService
from app.services.metric_service import MetricService


@app.post("/api/v1/analyze")
def analyze_scenario(request: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    HARA 보고서 생성 및 DB 저장.
    retrieve_context() 반환 구조:
      context_text : str           — LLM에 주입할 전체 텍스트
      source_docs  : List[dict]    — {"content":..., "metadata": {id, category, pattern, score}}
    """
    try:
        a_engine = get_analysis_engine()

        if request.mode == "base":
            if request.experiment_type == "sfha":
                sfha_engine = get_sfha_analysis_engine()
                result_text = sfha_engine.analyze_base(request.query)
            else:
                result_text = a_engine.analyze_base(request.query)
            source_docs = []

        else:
            r_engine = get_rag_engine()

            # 1. Knowledge 검색
            # retrieve_context()는 (context_text, source_docs) 튜플을 반환
            context_text, source_docs = r_engine.retrieve_context(request.query)

            # 2. LLM 분석
            if request.experiment_type == "sfha":
                sfha_engine = get_sfha_analysis_engine()
                llm_result = sfha_engine.analyze_rag(request.query, context_text)
            else:
                llm_result = a_engine.analyze_rag(request.query, context_text)

            # 3. RAG Context 요약 헤더 생성
            context_summary = "### [참조된 안전 지식 (RAG Context)]\n\n"
            if not source_docs:
                context_summary += "검색된 문헌이 없습니다.\n"
            else:
                for i, doc in enumerate(source_docs):
                    # rag_engine.py source_docs 구조:
                    # {"content": ..., "metadata": {"id":..,"category":..,"pattern":..,"score":..}}
                    meta     = doc.get("metadata", {})
                    score    = meta.get("score",    0.0)
                    category = meta.get("category", "N/A")
                    pattern  = meta.get("pattern",  "N/A")
                    doc_id   = meta.get("id",       "N/A")
                    context_summary += (
                        f"{i+1}. **[{doc_id}] {category}** - {pattern} "
                        f"(유사도: {score:.4f})\n"
                    )
            context_summary += "\n---\n\n"

            result_text = context_summary + llm_result

        # 4. 메트릭 계산 및 파싱
        metrics, parsed_rows = MetricService.evaluate_result(
            result_text, request.ground_truth
        )

        # 5. DB 저장
        db_result = AnalysisResult(
            query=request.query,
            mode=request.mode,
            result_text=result_text,
            parsed_data=json.dumps(parsed_rows, ensure_ascii=False),
            metrics=json.dumps(metrics,     ensure_ascii=False),
            ground_truth=request.ground_truth,
            is_saved=0,
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)

        return {
            "result":           result_text,
            "source_documents": source_docs,
            "metrics":          metrics,
            "parsed_data":      parsed_rows,
            "id":               db_result.id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze/{analysis_id}/save")
def save_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """분석 결과를 저장 상태로 표시"""
    try:
        analysis = db.query(AnalysisResult).filter(
            AnalysisResult.id == analysis_id
        ).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis result not found")

        analysis.is_saved = 1
        db.commit()
        return {"id": analysis.id, "message": "Analysis saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/history")
def get_history(limit: int = 10, db: Session = Depends(get_db)):
    """최근 저장된 분석 결과 반환"""
    results = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.is_saved == 1)
        .order_by(desc(AnalysisResult.created_at))
        .limit(limit)
        .all()
    )
    return results


@app.get("/api/v1/report")
def get_report(db: Session = Depends(get_db)):
    """저장된 HARA 행 집계 반환"""
    results = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.is_saved == 1)
        .order_by(desc(AnalysisResult.created_at))
        .all()
    )

    aggregated_rows = []
    for res in results:
        if res.parsed_data:
            try:
                rows = json.loads(res.parsed_data)
                for row in rows:
                    row["modelType"]  = "Base-LLM" if res.mode == "base" else "RAG-Model"
                    row["analysisId"] = res.id
                aggregated_rows.extend(rows)
            except Exception:
                pass

    return aggregated_rows


@app.get("/api/v1/evaluation")
def get_evaluation(db: Session = Depends(get_db)):
    """집계 메트릭 반환"""
    results = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.is_saved == 1)
        .order_by(desc(AnalysisResult.created_at))
        .all()
    )

    if not results:
        return {
            "cosineSimilarity": 0.0,
            "structureScore":   0.0,
            "complianceDetails": {
                "hasSituation": False, "hasHazard": False,
                "hasRiskAssessment": False, "hasASIL": False, "hasSafetyGoal": False,
            },
        }

    total_structure_score = 0.0
    total_cosine_score    = 0.0
    compliance_counts     = {
        "hasSituation": 0, "hasHazard": 0,
        "hasRiskAssessment": 0, "hasASIL": 0, "hasSafetyGoal": 0,
    }
    count = 0

    for res in results:
        if res.metrics:
            try:
                m = json.loads(res.metrics)
                total_structure_score += m.get("structureScore",   0)
                total_cosine_score    += m.get("cosineSimilarity", 0)
                details = m.get("complianceDetails", {})
                for k in compliance_counts:
                    if details.get(k):
                        compliance_counts[k] += 1
                count += 1
            except Exception:
                pass

    if count == 0:
        return {
            "cosineSimilarity": 0.0,
            "structureScore":   0.0,
            "complianceDetails": {k: False for k in compliance_counts},
        }

    return {
        "cosineSimilarity":  total_cosine_score    / count,
        "structureScore":    total_structure_score / count,
        "complianceDetails": {k: (v / count > 0.5) for k, v in compliance_counts.items()},
        "totalCount":        count,
    }


from app.db.models import AccidentMeta, AccidentNarrative

@app.get("/api/v1/accidents")
def get_accidents(limit: int = 50, db: Session = Depends(get_db)):
    """실험 선택용 사고 목록 반환"""
    results = (
        db.query(AccidentMeta, AccidentNarrative.description)
        .join(AccidentNarrative, AccidentMeta.report_id == AccidentNarrative.report_id)
        .filter(
            or_(
                cast(AccidentMeta.total_fatalities,   Integer) > 0,
                cast(AccidentMeta.all_injuries_count, Integer) > 0,
            ),
            func.length(AccidentMeta.primary_cause_text) > 2,
            AccidentMeta.primary_cause_code.in_(["22", "27", "30", "34", "85"]),
        )
        .limit(limit)
        .all()
    )

    data = []
    for meta, desc_text in results:
        data.append({
            "report_id":          meta.report_id,
            "event_type":         meta.event_type,
            "date":               meta.date or f"{meta.year}-{meta.month}-{meta.day}",
            "description":        desc_text,
            "primary_cause":      meta.primary_cause_text,
            "contributing_factor": meta.contributing_factor_text,
        })
    return data


from app.db.models import ManualEvaluation

class ManualEvaluationRequest(BaseModel):
    analysis_id:    int
    score:          int
    checklist_data: Dict[str, bool]
    evaluator:      Optional[str] = "User"

@app.post("/api/v1/evaluation/manual")
def save_manual_evaluation(
    request: ManualEvaluationRequest, db: Session = Depends(get_db)
):
    """수동 체크리스트 평가 저장"""
    try:
        analysis = db.query(AnalysisResult).filter(
            AnalysisResult.id == request.analysis_id
        ).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis result not found")

        existing_eval = db.query(ManualEvaluation).filter(
            ManualEvaluation.analysis_id == request.analysis_id
        ).first()

        if existing_eval:
            existing_eval.score          = request.score
            existing_eval.checklist_data = json.dumps(request.checklist_data)
            existing_eval.evaluator      = request.evaluator
            db.commit()
            return {"id": existing_eval.id, "message": "Evaluation updated successfully"}

        db_eval = ManualEvaluation(
            analysis_id=request.analysis_id,
            score=request.score,
            checklist_data=json.dumps(request.checklist_data),
            evaluator=request.evaluator,
        )
        db.add(db_eval)
        db.commit()
        db.refresh(db_eval)

        return {"id": db_eval.id, "message": "Evaluation saved successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))