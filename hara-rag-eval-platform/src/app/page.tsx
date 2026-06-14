'use client';

import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Typography, Divider, Spin } from 'antd';
import { TrophyOutlined, ExperimentOutlined, SafetyCertificateOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

interface DashboardMetrics {
  structureScore: number;
  complianceDetails: Record<string, boolean>;
  totalCount: number;
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/v1/evaluation');
        if (response.ok) {
          const data = await response.json();
          setMetrics(data);
        }
      } catch (error) {
        console.error('Failed to fetch dashboard metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-[calc(100vh-200px)]">
        <Spin size="large" />
        <div className="mt-4 text-gray-500">데이터 로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <Title level={2} style={{ marginBottom: 0 }}>HARA RAG 워크벤치</Title>
        <Paragraph className="text-gray-500 mt-2">
          RAG와 LLM을 활용한 HARA(Hazard Analysis and Risk Assessment) 자동화 및 평가 플랫폼
        </Paragraph>
      </div>

      <Row gutter={16}>
        <Col span={8}>
          <Card variant="borderless" className="shadow-sm">
            <Statistic
              title="총 실험 횟수"
              value={metrics?.totalCount || 0}
              prefix={<ExperimentOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card variant="borderless" className="shadow-sm">
            <Statistic
              title="구조적 적합성 (Compliance)"
              value={(metrics?.structureScore || 0) * 100}
              precision={1}
              styles={{ content: { color: '#cf1322' } }}
              prefix={<SafetyCertificateOutlined />}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <Title level={4}>프로젝트 개요</Title>
        <Divider />
        <Paragraph>
          이 플랫폼은 항공기 충돌 회피 시스템을 위한 HARA(위해 분석 및 리스크 평가) 프로세스를 자동화합니다.
          검색 증강 생성(RAG)을 활용하여 표준(ISO 26262 / ARP4761) 준수 여부와 위험 식별의 정확도를 기존 LLM 대비 향상시키는 것을 목표로 합니다.
        </Paragraph>
        <Paragraph>
          <strong>주요 목표:</strong>
          <ul>
            <li>아이템 정의(Item Definition)로부터 HARA 테이블 자동 생성</li>
            <li>NTSB 사고 리포트 메타데이터와 RAG 기반 출력 비교</li>
            <li>구조적 적합성 정량 평가</li>
          </ul>
        </Paragraph>
      </div>
    </div>
  );
}
