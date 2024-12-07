import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import styled from 'styled-components';

import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import CameraView from './pages/CameraView';
import AlertHistory from './pages/AlertHistory';
import Settings from './pages/Settings';

const { Content } = Layout;

const StyledLayout = styled(Layout)`
  min-height: 100vh;
`;

const StyledContent = styled(Content)`
  margin: 24px;
  padding: 24px;
  background: #fff;
  border-radius: 4px;
`;

function App() {
  return (
    <Router>
      <StyledLayout>
        <Sidebar />
        <Layout>
          <StyledContent>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/camera/:id" element={<CameraView />} />
              <Route path="/alerts" element={<AlertHistory />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </StyledContent>
        </Layout>
      </StyledLayout>
    </Router>
  );
}

export default App;
