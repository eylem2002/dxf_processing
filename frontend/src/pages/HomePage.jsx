import React, { useState } from 'react';
import DXFUploadForm from '../components/DXFUploadForm';
import DXFList from '../components/DXFList';

const HomePage = () => {
  const [refresh, setRefresh] = useState(false);
  const [projectId, setProjectId] = useState('');

  return (
    <div>
      <h2>Upload & View DXF Files</h2>
      <DXFUploadForm onUploadSuccess={() => setRefresh(!refresh)} />
      <input type="text" placeholder="Enter project ID" value={projectId} onChange={e => setProjectId(e.target.value)} />
      <DXFList projectId={projectId} key={refresh} />
    </div>
  );
};

export default HomePage;
