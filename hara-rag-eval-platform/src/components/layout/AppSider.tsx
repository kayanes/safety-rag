'use client';

import React from 'react';
import { Layout, Menu } from 'antd';
import { usePathname, useRouter } from 'next/navigation';
import {
    LayoutDashboard,
    TestTube,
    BarChart3,
    FileText
} from 'lucide-react';

const { Sider } = Layout;

const AppSider = () => {
    const router = useRouter();
    const pathname = usePathname();

    const items = [
        { key: '/', icon: <LayoutDashboard size={18} />, label: '대시보드' },
        { key: '/experiment', icon: <TestTube size={18} />, label: '실험(Experiment)-HARA' },
        { key: '/experiment-sfha', icon: <TestTube size={18} />, label: '실험(Experiment)-SFHA' },
        { key: '/evaluation', icon: <BarChart3 size={18} />, label: '평가 (Evaluation)' },
        { key: '/report', icon: <FileText size={18} />, label: 'HARA 리포트' },
    ];

    return (
        <Sider width={250} theme="light" className="h-screen fixed left-0 top-0 bottom-0 border-r border-gray-200">
            <div className="p-6 text-xl font-bold text-blue-600 flex items-center gap-2 border-b border-gray-100">
                <span>HARA Workbench</span>
            </div>
            <Menu
                mode="inline"
                selectedKeys={[pathname]}
                style={{ borderRight: 0 }}
                items={items.map(item => ({
                    ...item,
                    onClick: () => router.push(item.key)
                }))}
                className="mt-4"
            />
        </Sider>
    );
};

export default AppSider;
