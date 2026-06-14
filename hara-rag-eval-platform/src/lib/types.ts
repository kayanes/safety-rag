export interface HaraRow {
    id: string;
    function: string;
    malfunction: string;
    consequences: string;
    severity: 'S0' | 'S1' | 'S2' | 'S3';
    exposure: 'E0' | 'E1' | 'E2' | 'E3' | 'E4';
    controllability: 'C0' | 'C1' | 'C2' | 'C3';
    asil: 'QM' | 'A' | 'B' | 'C' | 'D';
    safetyGoal: string;
    safeState: string;
    modelType: 'Base-LLM' | 'RAG-Model';
}

export interface EvaluationMetrics {
    cosineSimilarity: number; // 0.0 to 1.0
    structureScore: number;   // 0.0 to 1.0
    complianceDetails: {
        hasSituation: boolean;
        hasHazard: boolean;
        hasRiskAssessment: boolean;
        hasASIL: boolean;
        hasSafetyGoal: boolean;
    };
}
