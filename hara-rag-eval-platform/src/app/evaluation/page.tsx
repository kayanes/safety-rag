'use client';

import React from 'react';
import { Card, Row, Col, Typography, Tag, Progress } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { MOCK_METRICS } from '@/lib/mock-data';

const { Title } = Typography;

// ... imports
import { useEffect, useState } from 'react';
import { Spin } from 'antd';

// ...

export default function EvaluationPage() {
    const [metrics, setMetrics] = useState<any>(MOCK_METRICS); // Initial state mock, then replace
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const response = await fetch('/api/v1/evaluation');
                if (response.ok) {
                    const result = await response.json();
                    setMetrics(result);
                }
            } catch (error) {
                console.error("Failed to fetch evaluation:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);



    const checklistItems = [
        { label: '상황 분석 (Situation Analysis)', passed: metrics.complianceDetails?.hasSituation },
        { label: '위해 식별 (Hazard Identification)', passed: metrics.complianceDetails?.hasHazard },
        { label: '리스크 평가 (S/E/C)', passed: metrics.complianceDetails?.hasRiskAssessment },
        { label: 'ASIL 결정', passed: metrics.complianceDetails?.hasASIL },
        { label: '안전 목표 (Safety Goal)', passed: metrics.complianceDetails?.hasSafetyGoal },
    ];

    if (loading) {
        return <div className="flex justify-center items-center h-screen"><Spin size="large" /></div>;
    }

    return (
        <div className="space-y-6">
            <Title level={2}>성능 평가 (Performance Evaluation)</Title>

            <Row gutter={[16, 16]}>
                <Col xs={24} md={12}>
                    <Card title="구조적 적합성 (Compliance)" className="h-full shadow-sm">
                        <Row gutter={16} align="middle">
                            <Col span={12} className="flex flex-col items-center justify-center">
                                <Progress
                                    type="dashboard"
                                    percent={Math.round((metrics.structureScore || 0) * 100)}
                                    strokeColor={(metrics.structureScore || 0) > 0.8 ? '#52c41a' : '#faad14'}
                                />
                                <div className="mt-2 font-semibold text-gray-600">총 적합성 점수</div>
                            </Col>
                            <Col span={12}>
                                <div className="flex flex-col">
                                    {checklistItems.map((item, index) => (
                                        <div key={index} className={`flex items-center gap-2 py-2 ${index < checklistItems.length - 1 ? 'border-b border-gray-100' : ''}`}>
                                            {item.passed ? <CheckCircleOutlined className="text-green-500" /> : <CloseCircleOutlined className="text-red-500" />}
                                            <span className={item.passed ? 'text-gray-800' : 'text-gray-400'}>{item.label}</span>
                                        </div>
                                    ))}
                                </div>
                            </Col>
                        </Row>
                        <p className="mt-8 text-gray-500 text-sm">
                            ISO 26262 Part 3 HARA 문서화 요구사항에 대한 준수 여부를 검사합니다.
                        </p>
                    </Card>
                </Col>

                <Col xs={24} md={12}>

                </Col>
            </Row>
        </div>
    );
}
