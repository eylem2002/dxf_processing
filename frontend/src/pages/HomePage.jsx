import React, { useState } from 'react';
import DXFUploadForm from '../components/DXFUploadForm';
import DXFList from '../components/DXFList';

const HomePage = () => {
  const [refresh, setRefresh] = useState(false);
  const [projectId, setProjectId] = useState('');

  return (
    <div style={{ maxWidth: '700px', margin: 'auto', padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2 style={{ textAlign: 'center' }}>Upload & View DXF Files</h2>

      {/* Pass projectId and setProjectId to keep it synced */}
      <DXFUploadForm projectId={projectId} setProjectId={setProjectId} onUploadSuccess={() => setRefresh(!refresh)} />

      <div style={{ marginTop: '30px' }}>
        <label htmlFor="projectIdInput" style={{ fontWeight: 'bold' }}>Filter by Project ID:</label>
        <input
          id="projectIdInput"
          type="text"
          placeholder="Enter project ID"
          value={projectId}
          onChange={e => setProjectId(e.target.value)}
          style={{ marginLeft: '10px', padding: '6px 10px', fontSize: '14px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
      </div>

      <DXFList projectId={projectId} key={refresh} />
    </div>
  );
};

export default HomePage;
