import { HaraRow, EvaluationMetrics } from './types';

export const MOCK_HARA_DATA: HaraRow[] = [
    {
        id: 'H-001',
        function: '충돌 회피 (Collision Avoidance)',
        malfunction: '장애물 감지 실패 (Failure to detect obstacle)',
        consequences: '지형 또는 물체와 충돌 (Collision with terrain or object)',
        severity: 'S3',
        exposure: 'E4',
        controllability: 'C3',
        asil: 'D',
        safetyGoal: '시스템은 99.9% 정확도로 장애물을 감지해야 함 (System must detect obstacles with 99.9% accuracy)',
        safeState: '조종사에게 경고 및 회피 기동 시작 (Alert pilot and initiate fallback maneuver)',
        modelType: 'RAG-Model',
    },
    {
        id: 'H-001-BASE',
        function: '충돌 회피 (Collision Avoidance)',
        malfunction: '장애물 감지 실패 (Failure to detect obstacle)',
        consequences: '충돌 가능성 있음 (Possible collision)',
        severity: 'S3',
        exposure: 'E4',
        controllability: 'C3',
        asil: 'B', // Deliberate error for demo
        safetyGoal: '충돌 회피 (Avoid collision)',
        safeState: '수동 제어 (Manual control)',
        modelType: 'Base-LLM',
    },
];

export const MOCK_METRICS: EvaluationMetrics = {
    cosineSimilarity: 0.91,
    structureScore: 0.85,
    complianceDetails: {
        hasSituation: true,
        hasHazard: true,
        hasRiskAssessment: true,
        hasASIL: true,
        hasSafetyGoal: true,
    },
};
