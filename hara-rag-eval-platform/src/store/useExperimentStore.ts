import { create } from 'zustand';
import { HaraRow, EvaluationMetrics } from '@/lib/types';
import { MOCK_HARA_DATA, MOCK_METRICS } from '@/lib/mock-data';

export interface AccidentData {
    report_id: string;
    event_type: string;
    date: string;
    description: string;
    primary_cause: string;
    contributing_factor: string;
}

interface ExperimentState {
    modelType: 'Base-LLM' | 'RAG-Model';
    itemDefinition: string;
    contextFile: File | null;
    results: HaraRow[];
    baseOutput: string;
    ragOutput: string;
    citations: any[];
    baseIsRunning: boolean;
    ragIsRunning: boolean;
    baseIsSaved: boolean;
    ragIsSaved: boolean;
    checklistState: Record<'base' | 'rag', Record<string, number>>;
    setItemDefinition: (text: string) => void;
    setChecklistItemScore: (id: string, model: 'base' | 'rag', score: number) => void;
    runAnalysis: (target?: 'both' | 'base' | 'rag') => Promise<void>;
    baseAnalysisId: string | null;
    ragAnalysisId: string | null;
    saveAnalysisResult: (model: 'base' | 'rag') => Promise<void>;
    saveChecklist: (model: 'base' | 'rag') => Promise<void>;
}

export const useExperimentStore = create<ExperimentState>((set, get) => ({
    modelType: 'RAG-Model',
    itemDefinition: '',
    contextFile: null,
    results: [],
    baseOutput: '',
    ragOutput: '',
    citations: [],
    baseIsRunning: false,
    ragIsRunning: false,
    baseIsSaved: false,
    ragIsSaved: false,
    checklistState: { base: {}, rag: {} },
    setItemDefinition: (text) => set({ itemDefinition: text }),
    setChecklistItemScore: (id, model, score) => set((state) => ({
        checklistState: {
            ...state.checklistState,
            [model]: {
                ...state.checklistState[model],
                [id]: score
            }
        }
    })),
    baseAnalysisId: null,
    ragAnalysisId: null,
    saveAnalysisResult: async (model: 'base' | 'rag') => {
        const state = get();
        const analysisId = model === 'base' ? state.baseAnalysisId : state.ragAnalysisId;
        if (!analysisId) {
            throw new Error("분석 결과 ID가 없습니다.");
        }

        try {
            const response = await fetch(`http://localhost:8000/api/v1/analyze/${analysisId}/save`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error("결과 저장에 실패했습니다.");
            }
            if (model === 'base') set({ baseIsSaved: true });
            else set({ ragIsSaved: true });
        } catch (error) {
            console.error("Error saving analysis result:", error);
            throw error;
        }
    },
    saveChecklist: async (model: 'base' | 'rag') => {
        const state = get();
        const analysisId = model === 'base' ? state.baseAnalysisId : state.ragAnalysisId;
        const checklist = state.checklistState[model];
        const checkedCount = Object.values(checklist).reduce((acc, val) => acc + val, 0);

        if (!analysisId) {
            throw new Error("분석 결과 ID가 없습니다. 먼저 분석을 실행해주세요.");
        }

        const payload = {
            analysis_id: analysisId,
            score: checkedCount,
            checklist_data: checklist,
            evaluator: "User"
        };

        try {
            const response = await fetch('http://localhost:8000/api/v1/evaluation/manual', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const text = await response.text();
                console.error("Save failed:", text);
                throw new Error("평가 저장에 실패했습니다.");
            }
        } catch (error) {
            console.error("Error saving checklist:", error);
            throw error;
        }
    },
    runAnalysis: async (target: 'both' | 'base' | 'rag' = 'both') => {
        const { itemDefinition } = get();

        // Validation: Item Definition is always required as the "Task"
        if (!itemDefinition) {
            alert("아이템 정의(Task)를 입력해주세요.");
            return;
        }

        const runBase = target === 'both' || target === 'base';
        const runRag = target === 'both' || target === 'rag';

        if (runBase) {
            set({ baseIsRunning: true, baseOutput: '', baseAnalysisId: null, baseIsSaved: false });
        }
        if (runRag) {
            set({ ragIsRunning: true, ragOutput: '', citations: [], ragAnalysisId: null, ragIsSaved: false });
        }

        const fetchAnalysis = async (mode: 'rag' | 'base') => {
            const payload = {
                query: itemDefinition, // The Task
                mode: mode,
            };

            try {
                const response = await fetch('http://localhost:8000/api/v1/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });

                if (!response.ok) {
                    let errorMsg = 'Analysis failed';
                    try {
                        const text = await response.text();
                        try {
                            const errorData = JSON.parse(text);
                            errorMsg = errorData.detail || errorMsg;
                        } catch {
                            console.error("Non-JSON API Error:", text.slice(0, 200));
                            errorMsg = `API Error: ${response.status} ${response.statusText}`;
                        }
                    } catch (e) {
                        errorMsg = `API Error: ${response.status} ${response.statusText}`;
                    }
                    throw new Error(errorMsg);
                }

                const data = await response.json();
                return data;
            } catch (error) {
                console.error(`Analysis error (${mode}):`, error);
                throw error;
            }
        };

        // Run selectively
        const promises = [];
        if (runRag) promises.push(fetchAnalysis('rag'));
        if (runBase) promises.push(fetchAnalysis('base'));

        const results = await Promise.allSettled(promises);

        let resultIndex = 0;

        // Handle RAG Result
        if (runRag) {
            const ragResult = results[resultIndex++];
            if (ragResult.status === 'fulfilled') {
                set({
                    ragOutput: ragResult.value.result,
                    citations: ragResult.value.source_documents || [],
                    ragAnalysisId: ragResult.value.id
                });
            } else {
                set({
                    ragOutput: `Error: ${ragResult.reason instanceof Error ? ragResult.reason.message : 'Unknown error'}`
                });
            }
            set({ ragIsRunning: false });
        }

        // Handle Base Result
        if (runBase) {
            const baseResult = results[resultIndex++];
            if (baseResult.status === 'fulfilled') {
                set({
                    baseOutput: baseResult.value.result,
                    baseAnalysisId: baseResult.value.id
                });
            } else {
                set({
                    baseOutput: `Error: ${baseResult.reason instanceof Error ? baseResult.reason.message : 'Unknown error'}`
                });
            }
            set({ baseIsRunning: false });
        }
    },
}));

export const CHECKLIST_ITEMS = [
    {
        area: "HARA 개념 이해",
        items: [
            { id: "hara-understanding", title: "HARA 정의의 정확성", desc: "HARA의 목적과 개념이 ISO 26262 기준에 맞게 설명되었는가" }
        ]
    },
    {
        area: "시스템 기능 정의",
        items: [
            { id: "system-function", title: "시스템 주요 기능 식별", desc: "분석 대상 시스템의 주요 기능이 명확하게 제시되었는가" }
        ]
    },
    {
        area: "운용 상황 정의",
        items: [
            { id: "operational-situation", title: "Operational Situation 명확성", desc: "운용 상황(비행 단계, 환경 등)이 구체적으로 기술되었는가" }
        ]
    },
    {
        area: "오작동 정의",
        items: [
            { id: "malfunction", title: "Malfunction 식별", desc: "시스템 기능과 관련된 오작동이 명확하게 식별되었는가" }
        ]
    },
    {
        area: "Hazard 정의",
        items: [
            { id: "hazard", title: "Hazard 도출", desc: "시스템 오작동으로 인해 발생 가능한 위험 상태가 정의되었는가" }
        ]
    },
    {
        area: "Hazardous Event 정의",
        items: [
            { id: "hazardous-event", title: "Hazardous Event 구성", desc: "운용 상황 + 오작동 + Hazard가 논리적으로 결합되어 정의되었는가" }
        ]
    },
    {
        area: "Severity 평가",
        items: [
            { id: "severity", title: "Severity 평가 타당성", desc: "위험 결과의 심각도가 합리적으로 평가되었는가" }
        ]
    },
    {
        area: "Exposure 평가",
        items: [
            { id: "exposure", title: "Exposure 평가 타당성", desc: "해당 상황의 발생 가능성이 논리적으로 설명되었는가" }
        ]
    },
    {
        area: "Controllability 평가",
        items: [
            { id: "controllability", title: "Controllability 평가 타당성", desc: "조종사 또는 시스템이 위험을 통제할 가능성이 평가되었는가" }
        ]
    },
    {
        area: "ASIL 도출",
        items: [
            { id: "asil", title: "ASIL 결정 논리", desc: "S/E/C 평가를 기반으로 ASIL이 논리적으로 도출되었는가" }
        ]
    },
    {
        area: "Safety Goal 정의",
        items: [
            { id: "safety-goal", title: "Safety Goal 적절성", desc: "위험을 완화하기 위한 안전 목표가 명확히 제시되었는가" }
        ]
    },
    {
        area: "Safe State 정의",
        items: [
            { id: "safe-state", title: "Safe State 명확성", desc: "시스템이 도달해야 할 안전 상태가 정의되었는가" }
        ]
    }
];
