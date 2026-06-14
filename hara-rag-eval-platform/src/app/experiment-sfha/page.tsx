'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
    Select,
    Input,
    Upload,
    Button,
    Tabs,
    Card,
    Splitter,
    Typography,
    Tag,
    Divider,
    Segmented,
    Modal,
    Skeleton,
    message,
    Table
} from 'antd';
import { UploadOutlined, ThunderboltOutlined, CheckCircleFilled, DatabaseOutlined, SaveOutlined, BarChartOutlined } from '@ant-design/icons'; // Added BarChartOutlined
import { useExperimentSfhaStore, CHECKLIST_ITEMS } from '@/store/useExperimentSfhaStore';

const { TextArea } = Input;
const { Title } = Typography;

export default function ExperimentSFHAPage() {
    const {
        itemDefinition, setItemDefinition,
        runAnalysis, baseIsRunning, ragIsRunning,
        baseIsSaved, ragIsSaved, saveAnalysisResult,
        baseOutput, ragOutput,
        citations,
        checklistState, setChecklistItemScore,
        saveChecklist, baseAnalysisId, ragAnalysisId
    } = useExperimentSfhaStore();

    const [evalModel, setEvalModel] = useState<'base' | 'rag'>('base');
    const [isSaving, setIsSaving] = useState(false);

    const handleSaveChecklist = async () => {
        try {
            setIsSaving(true);
            await saveChecklist(evalModel);
            message.success(`${evalModel === 'rag' ? 'RAG 모델' : '기본 LLM'} 평가 결과가 저장되었습니다.`);
        } catch (error) {
            message.error("평가 저장 중 오류가 발생했습니다.");
        } finally {
            setIsSaving(false);
        }
    };



    const markdownComponents = {
        h1: ({ node, ...props }: any) => <h1 className="text-2xl font-bold mt-4 mb-2" {...props} />,
        h2: ({ node, ...props }: any) => <h2 className="text-xl font-bold mt-3 mb-2" {...props} />,
        h3: ({ node, ...props }: any) => <h3 className="text-lg font-bold mt-2 mb-1" {...props} />,
        p: ({ node, ...props }: any) => <p className="mb-2 leading-relaxed whitespace-pre-wrap" {...props} />,
        ul: ({ node, ...props }: any) => <ul className="list-disc pl-5 mb-2" {...props} />,
        ol: ({ node, ...props }: any) => <ol className="list-decimal pl-5 mb-2" {...props} />,
        li: ({ node, ...props }: any) => <li className="mb-1" {...props} />,
        table: ({ node, ...props }: any) => <div className="overflow-x-auto mb-4 border rounded-lg"><table className="min-w-full divide-y divide-gray-200" {...props} /></div>,
        th: ({ node, ...props }: any) => <th className="px-3 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b font-bold" {...props} />,
        td: ({ node, ...props }: any) => <td className="px-3 py-2 text-sm text-gray-700 border-b align-top" {...props} />,
        blockquote: ({ node, ...props }: any) => <blockquote className="border-l-4 border-gray-300 pl-4 italic my-2" {...props} />,
        strong: ({ node, ...props }: any) => <strong className="font-semibold" {...props} />,
    };

    const contextColumns = [
        { title: 'ID', dataIndex: ['metadata', 'id'], key: 'id', width: 90 },
        { title: 'Hazard Pattern', dataIndex: ['metadata', 'pattern'], key: 'pattern', width: 200 },
        {
            title: 'Similarity Score',
            dataIndex: ['metadata', 'score'],
            key: 'score',
            width: 140,
            render: (val: number) => val ? val.toFixed(4) : '-'
        },
        { title: 'Knowledge Context', dataIndex: 'content', key: 'content' }
    ];

    return (
        <div className="min-h-screen bg-gray-50 p-8 space-y-8">
            <div>
                <Title level={2} style={{ margin: 0 }}>실험(Experiment)-SFHA</Title>
                <div className="text-gray-500 mt-2">RAG 모델의 성능을 평가하고 비교해보세요</div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left Panel: Configuration */}
                <div className="lg:col-span-4 space-y-6">
                    <Card
                        title="실험 설정 (Experiment Configuration)"
                        className="shadow-sm border-gray-200"
                        styles={{ header: { borderBottom: '1px solid #f0f0f0', backgroundColor: 'white' }, body: { padding: '24px' } }}
                    >
                        <div className="space-y-6">


                            {/* Item Definition (Task) */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">아이템 정의 (Task / Query)</label>
                                <TextArea
                                    rows={6}
                                    value={itemDefinition}
                                    onChange={(e) => setItemDefinition(e.target.value)}
                                    placeholder="분석할 아이템에 대한 설명이나 구체적인 태스크를 입력하세요..."
                                    className="text-sm rounded-md"
                                />
                            </div>


                            <Button
                                type="primary"
                                icon={<ThunderboltOutlined />}
                                block
                                size="large"
                                onClick={() => runAnalysis('both')}
                                loading={baseIsRunning || ragIsRunning}
                                disabled={!itemDefinition} // Require Task input
                                className="h-12 text-lg font-medium bg-blue-600 hover:bg-blue-700 border-none rounded-md mt-4"
                            >
                                전체 분석 시작 (Run All)
                            </Button>
                        </div>
                    </Card>
                </div>




                {/* Right Panel: Results */}
                <div className="lg:col-span-8 space-y-8">
                    {/* Comparison View */}
                    <div>
                        <h3 className="text-lg font-bold text-gray-800 mb-4">비교 보기 (Side-by-Side)</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Base LLM Output */}
                            <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 min-h-[500px] flex flex-col">
                                <div className="flex justify-between items-center border-b border-amber-200 pb-2 mb-4">
                                    <div className="flex items-center gap-2 font-semibold text-amber-700">
                                        <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                                        기본 LLM 출력
                                    </div>
                                    <div className="flex gap-2">
                                        <Button size="small" onClick={() => runAnalysis('base')} loading={baseIsRunning} disabled={baseIsRunning || ragIsRunning || !itemDefinition}>
                                            재실행
                                        </Button>
                                        <Button
                                            size="small"
                                            type="primary"
                                            onClick={() => saveAnalysisResult('base')}
                                            disabled={!baseAnalysisId || baseIsSaved}
                                            icon={<SaveOutlined />}
                                        >
                                            {baseIsSaved ? '저장됨' : '결과 저장'}
                                        </Button>
                                    </div>
                                </div>
                                {baseOutput ? (
                                    <div className="text-gray-700 markdown-body text-sm flex-1 overflow-y-auto max-h-[600px] pr-2">
                                        <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{baseOutput}</ReactMarkdown>
                                    </div>
                                ) : (
                                    <div className="text-amber-400 text-center mt-32 text-sm">
                                        분석을 시작하여 결과를 확인하세요...
                                    </div>
                                )}
                            </div>

                            {/* RAG Output */}
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 min-h-[500px] flex flex-col">
                                <div className="flex justify-between items-center border-b border-blue-200 pb-2 mb-4">
                                    <div className="flex items-center gap-2 font-semibold text-blue-700">
                                        <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                                        RAG 출력
                                    </div>
                                    <div className="flex gap-2">
                                        <Button size="small" onClick={() => runAnalysis('rag')} loading={ragIsRunning} disabled={baseIsRunning || ragIsRunning || !itemDefinition}>
                                            재실행
                                        </Button>
                                        <Button
                                            size="small"
                                            type="primary"
                                            onClick={() => saveAnalysisResult('rag')}
                                            disabled={!ragAnalysisId || ragIsSaved}
                                            icon={<SaveOutlined />}
                                        >
                                            {ragIsSaved ? '저장됨' : '결과 저장'}
                                        </Button>
                                    </div>
                                </div>
                                {ragOutput ? (
                                    <div className="text-gray-800 flex-1 overflow-y-auto max-h-[600px] pr-2">

                                        {citations && citations.length > 0 && (
                                            <div className="mb-6 border border-blue-200 rounded-md overflow-hidden bg-white shadow-sm">
                                                <div className="bg-blue-50 px-4 py-2 border-b border-blue-200 font-bold text-blue-900 text-sm">
                                                    Retrieved Context (Top-{citations.length})
                                                </div>
                                                <Table
                                                    dataSource={citations}
                                                    columns={contextColumns}
                                                    pagination={false}
                                                    size="small"
                                                    rowKey={(record: any, index: any) => record?.metadata?.id || index}
                                                    className="m-0"
                                                />
                                            </div>
                                        )}

                                        <div className="markdown-body text-sm">
                                            <h3 className="text-lg font-bold mb-4 border-b pb-2">HARA Analysis Result</h3>
                                            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{ragOutput}</ReactMarkdown>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="text-blue-400 text-center mt-32 text-sm">
                                        분석을 시작하여 결과를 확인하세요...
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* HARA Compliance Evaluation */}
                    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden flex flex-col h-full">
                        {/* Header */}
                        <div className="p-5 border-b border-gray-100 flex justify-between items-start">
                            <div>
                                <Title level={3} style={{ margin: 0, fontWeight: 700 }}>HARA 준수성 평가</Title>
                                <div className="text-gray-500 text-sm mt-1">ISO 26262 기반 (총 {CHECKLIST_ITEMS.reduce((acc, group) => acc + group.items.length * 2, 0)}점)</div>
                            </div>
                            <Button
                                type="default"
                                icon={<BarChartOutlined />}
                                onClick={handleSaveChecklist}
                                loading={isSaving}
                                disabled={!(evalModel === 'base' ? baseIsSaved : ragIsSaved)}
                                className="bg-gray-50"
                            >
                                결과 보기
                            </Button>
                        </div>

                        <div className="p-5 space-y-4 bg-gray-50/50">
                            {/* Toggle */}
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setEvalModel('base')}
                                    className={`flex-1 py-2.5 rounded-md font-medium text-sm transition-all border ${evalModel === 'base' ? 'bg-amber-500 text-white border-amber-600 shadow-sm' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}
                                >
                                    기본 LLM
                                </button>
                                <button
                                    onClick={() => setEvalModel('rag')}
                                    className={`flex-1 py-2.5 rounded-md font-medium text-sm transition-all border ${evalModel === 'rag' ? 'bg-blue-500 text-white border-blue-600 shadow-sm' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}
                                >
                                    RAG 모델
                                </button>
                            </div>

                            {/* Score Card */}
                            {(() => {
                                const currentScore = Object.values(checklistState[evalModel] || {}).reduce((sum, val) => sum + val, 0);
                                const maxScore = CHECKLIST_ITEMS.reduce((acc, group) => acc + group.items.length * 2, 0);
                                const isRag = evalModel === 'rag';
                                return (
                                    <div className={`rounded-lg p-5 flex justify-between items-center border ${isRag ? 'bg-blue-50 border-blue-200' : 'bg-amber-50 border-amber-200'}`}>
                                        <div>
                                            <h3 className="text-base font-bold text-gray-800 m-0">{isRag ? 'RAG 모델 평가' : '기본 LLM 평가'}</h3>
                                            <p className="text-sm text-gray-500 m-0 mt-1">ISO 26262 기반</p>
                                        </div>
                                        <div className="text-right">
                                            <div className={`text-2xl font-bold leading-none mb-1 ${isRag ? 'text-blue-600' : 'text-amber-600'}`}>
                                                {currentScore}<span className={`text-lg ${isRag ? 'text-blue-400' : 'text-amber-400'}`}>/{maxScore}</span>
                                            </div>
                                            <div className="text-xs text-gray-500 font-medium">
                                                {Math.round((currentScore / maxScore) * 100)}%
                                            </div>
                                        </div>
                                    </div>
                                );
                            })()}

                            {/* Legend */}
                            <div className="flex justify-center items-center py-2 bg-white rounded-md border border-gray-200 text-sm gap-4 shadow-sm">
                                <span className="flex items-center gap-1.5"><span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 border border-gray-200 rounded text-xs font-bold">0</span> 미충족</span>
                                <span className="flex items-center gap-1.5"><span className="px-1.5 py-0.5 bg-yellow-50 text-yellow-600 border border-yellow-200 rounded text-xs font-bold">1</span> 부분</span>
                                <span className="flex items-center gap-1.5"><span className="px-1.5 py-0.5 bg-green-50 text-green-600 border border-green-200 rounded text-xs font-bold">2</span> 완전</span>
                            </div>
                        </div>

                        {/* Items List */}
                        <div className="flex-1 overflow-y-auto p-5 pt-0 bg-gray-50/50 space-y-4 max-h-[800px]">
                            {CHECKLIST_ITEMS.flatMap((group) => group.items.map((item) => {
                                const val = checklistState[evalModel]?.[item.id] || 0;
                                return (
                                    <div key={item.id} className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
                                        <div className="flex items-center gap-3 mb-3">
                                            <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs font-medium border border-gray-200">
                                                {group.area}
                                            </span>
                                            <span className="font-bold text-green-600 text-lg leading-none">{val}/2</span>
                                        </div>
                                        <h4 className="text-base font-bold text-gray-900 m-0">{item.title}</h4>
                                        <p className="text-sm text-gray-500 mt-1 mb-4">{item.desc}</p>

                                        <div className="flex gap-2">
                                            {[0, 1, 2].map(score => {
                                                const isSelected = val === score;
                                                return (
                                                    <button
                                                        key={score}
                                                        onClick={() => setChecklistItemScore(item.id, evalModel, score)}
                                                        className={`flex-1 py-1.5 rounded-md text-sm font-medium transition-colors border ${isSelected ? 'bg-green-50 text-green-600 border-green-500' : 'bg-gray-50 text-gray-500 border-gray-200 hover:bg-gray-100'}`}
                                                    >
                                                        {score}점
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </div>
                                );
                            }))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
