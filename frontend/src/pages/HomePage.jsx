// src/pages/HomePage.jsx

import React, { useState } from 'react';
import DXFUploadForm from '../components/DXFUploadForm';
import KeywordTreeGenerator from '../components/KeywordTreeGenerator';

const HomePage = () => {
  const [step, setStep]       = useState(1);
  const [currentPlanId, setCurrentPlanId] = useState('');

  return (
    <div style={{ maxWidth: 700, margin: 'auto', padding: 20, fontFamily: 'Arial, sans-serif' }}>
      <h2 style={{ textAlign: 'center' }}>DXF Workflow</h2>

      {step === 1 && (
        <DXFUploadForm
          projectId={currentPlanId}        // only used to link the DXF
          setProjectId={setCurrentPlanId}  // so the form knows which project to link it to
          onUploadSuccess={(planIds) => {
            setCurrentPlanId(planIds[0]);  // pick the first returned planId
            setStep(2);
          }}
        />
      )}

      {step === 2 && (
        <KeywordTreeGenerator planId={currentPlanId} />
      )}
    </div>
  );
};

export default HomePage;
