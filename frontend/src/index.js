import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import BrainTumorDetectionApp from './brain-tumor-detection';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrainTumorDetectionApp />
  </React.StrictMode>
);
