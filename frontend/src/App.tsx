import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppShell from './components/layout/AppShell';
import LoginPage from './pages/LoginPage';
import DatasetsPage from './pages/DatasetsPage';
import DatasetDetailPage from './pages/DatasetDetailPage';
import PipelinesPage from './pages/PipelinesPage';
import PipelineDetailPage from './pages/PipelineDetailPage';
import MonitoringPage from './pages/MonitoringPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<AppShell />}>
            <Route index element={<Navigate to="/datasets" replace />} />
            <Route path="/datasets" element={<DatasetsPage />} />
            <Route path="/datasets/:id" element={<DatasetDetailPage />} />
            <Route path="/pipelines" element={<PipelinesPage />} />
            <Route path="/pipelines/:id" element={<PipelineDetailPage />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
