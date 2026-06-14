'use client';

import React from 'react';
import { Layout } from 'antd';
import AppSider from './AppSider';

const { Content } = Layout;

const AppLayout = ({ children }: { children: React.ReactNode }) => {
    return (
        <Layout style={{ minHeight: '100vh' }}>
            <AppSider />
            <Layout style={{ marginLeft: 0 }}>
                <Content style={{ margin: '24px 5px 0', overflow: 'initial' }}>
                    <div className="p-6 min-h-full">
                        {children}
                    </div>
                </Content>
            </Layout>
        </Layout>
    );
};

export default AppLayout;
