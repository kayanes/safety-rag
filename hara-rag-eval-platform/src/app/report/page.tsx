'use client';

import React from 'react';
import { Table, Tag, Button, Typography, Space } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { MOCK_HARA_DATA } from '@/lib/mock-data';
import type { ColumnsType } from 'antd/es/table';
import { HaraRow } from '@/lib/types';

const { Title } = Typography;

const columns: ColumnsType<HaraRow> = [
    {
        title: 'ID',
        dataIndex: 'id',
        key: 'id',
        width: 100,
        fixed: 'left',
    },
    {
        title: '생성 모델 (Model)',
        dataIndex: 'modelType',
        key: 'modelType',
        width: 140,
        render: (text) => {
            const isRag = text === 'RAG-Model';
            return <Tag color={isRag ? 'blue' : 'volcano'}>{text || 'Unknown'}</Tag>;
        }
    },
    {
        title: '기능 (Function)',
        dataIndex: 'function',
        key: 'function',
        width: 150,
    },
    {
        title: '오작동 (Malfunction)',
        dataIndex: 'malfunction',
        key: 'malfunction',
        width: 200,
    },
    {
        title: '영향 (Consequences)',
        dataIndex: 'consequences',
        key: 'consequences',
        width: 250,
    },
    {
        title: 'S',
        dataIndex: 'severity',
        key: 'severity',
        width: 60,
        align: 'center',
        render: (text) => <Tag color="volcano">{text}</Tag>
    },
    {
        title: 'E',
        dataIndex: 'exposure',
        key: 'exposure',
        width: 60,
        align: 'center',
        render: (text) => <Tag color="geekblue">{text}</Tag>
    },
    {
        title: 'C',
        dataIndex: 'controllability',
        key: 'controllability',
        width: 60,
        align: 'center',
        render: (text) => <Tag color="green">{text}</Tag>
    },
    {
        title: 'ASIL',
        dataIndex: 'asil',
        key: 'asil',
        width: 80,
        align: 'center',
        render: (text) => {
            let color = 'default';
            if (text === 'A') color = 'green';
            if (text === 'B') color = 'gold';
            if (text === 'C') color = 'orange';
            if (text === 'D') color = 'red';
            return <Tag color={color} className="font-bold">{text}</Tag>;
        }
    },
    {
        title: '안전 목표 (Safety Goal)',
        dataIndex: 'safetyGoal',
        key: 'safetyGoal',
        width: 300,
    },
];

// ... imports
import { useEffect, useState } from 'react';

// ... columns definition

export default function ReportPage() {
    const [data, setData] = useState<(HaraRow & { key: string })[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const response = await fetch('/api/v1/report');
                if (response.ok) {
                    const result: HaraRow[] = await response.json();
                    const dataWithKeys = result.map((item, index) => ({
                        ...item,
                        key: `${item.id}-${index}`
                    }));
                    setData(dataWithKeys);
                }
            } catch (error) {
                console.error("Failed to fetch report:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleExport = () => {
        const csvContent = "data:text/csv;charset=utf-8,"
            + "ID,Model,Function,Malfunction,ASIL,Safety Goal\n"
            + data.map(e => `${e.id},${e.modelType},${e.function},${e.malfunction},${e.asil},"${e.safetyGoal}"`).join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "hari_report.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <Title level={2}>HARA 분석 결과 리포트</Title>
                <Button type="primary" icon={<DownloadOutlined />} onClick={handleExport} disabled={data.length === 0}>
                    CSV 다운로드
                </Button>
            </div>

            <Table
                columns={columns}
                dataSource={data}
                rowKey="key"
                scroll={{ x: 'max-content' }}
                bordered
                pagination={{ pageSize: 10 }}
                loading={loading}
                className="shadow-sm bg-white rounded-lg"
            />
        </div>
    );
}
