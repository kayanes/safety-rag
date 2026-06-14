import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import StyledComponentsRegistry from '@/lib/AntdRegistry';
import { ConfigProvider } from 'antd';
import theme from '@/theme/themeConfig';
import AppLayout from '@/components/layout/AppLayout';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'HARA RAG Workbench',
  description: 'Safety analysis automation and evaluation platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <StyledComponentsRegistry>
          <ConfigProvider theme={theme}>
            <AppLayout>
              {children}
            </AppLayout>
          </ConfigProvider>
        </StyledComponentsRegistry>
      </body>
    </html>
  );
}
