import React, { useState } from 'react';
import DXFUploadForm from '../components/DXFUploadForm';
import DXFList from '../components/DXFList';
import KeywordTreeGenerator from '../components/KeywordTreeGenerator';
import DXFDetail from '../components/DXFDetail';

const HomePage = () => {
  const [step, setStep] = useState(1);
  const [projectId, setProjectId] = useState('');
  const [tempPath, setTempPath] = useState('');
  const [availableKeywords, setAvailableKeywords] = useState([]);
  const [planId, setPlanId] = useState('');

  // after upload: capture tempPath and keywords
  const handleUploadSuccess = (path, keywords) => {
    setTempPath(path);
    setAvailableKeywords(keywords);
    setStep(2);
  };

  // selecting an existing saved plan
  const handleSelectExisting = id => {
    setPlanId(id);
    setStep(4);
  };

  // after preview+store
  const handleComplete = id => {
    setPlanId(id);
    setStep(4);
  };

  return (
    <div style={{ maxWidth: 700, margin: 'auto', padding: 20 }}>
      <h2 style={{ textAlign: 'center' }}>DXF Workflow</h2>

      {step === 1 && (
        <>
          <DXFUploadForm
            projectId={projectId}
            setProjectId={setProjectId}
            onUploadSuccess={handleUploadSuccess}
          />

          <hr style={{ margin: '40px 0' }} />

          <h3>Or select an existing plan:</h3>
          <DXFList
            projectId={projectId}
            onSelectPlan={handleSelectExisting}
          />
        </>
      )}

      {step === 2 && (
        <KeywordTreeGenerator
          tempPath={tempPath}
          projectId={projectId}
          availableKeywords={availableKeywords}
          onComplete={handleComplete}
        />
      )}

      {step === 4 && (
        <>
          <h3>Floor Plan Detail</h3>
          <p><strong>Plan ID:</strong> {planId}</p>
          <DXFDetail planId={planId} />
        </>
      )}
    </div>
  );
};

export default HomePage;
