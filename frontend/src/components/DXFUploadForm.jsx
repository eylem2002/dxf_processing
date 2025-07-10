import React, { useState } from 'react';
import axios from 'axios';

const DXFUploadForm = ({ projectId, setProjectId, onUploadSuccess }) => {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleFileChange = e => {
    // to avoid duplicates
    const selected = Array.from(e.target.files).filter(
      f => !files.some(x => x.name === f.name)
    );
    setFiles(prev => [...prev, ...selected]);
    e.target.value = null;
  };

  const removeFile = idx => {
    setFiles(prev => prev.filter((_, i) => i !== idx));
  };

  const handleUpload = async () => {
    if (!projectId.trim()) {
      alert('Project ID is required.');
      return;
    }
    if (files.length === 0) {
      alert('Select at least one DXF file.');
      return;
    }

    setLoading(true);
    setMessage('Uploading…');

    const formData = new FormData();
    files.forEach(f => formData.append('files', f));

    try {
      const res = await axios.post('/process_dxf/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const tempMap = res.data.temp_files || {};
      const tempIds = Object.keys(tempMap);
      if (tempIds.length === 0) throw new Error('No temp files returned.');
      const tempPath = tempMap[tempIds[0]];
      const meaningfulBlock = res.data.meaningful_block_keywords || [];
      const allBlock       = res.data.all_block_keywords       || [];
      const meaningfulLayer= res.data.meaningful_layer_keywords || [];
      const allLayer       = res.data.all_layer_keywords       || [];

      setFiles([]);
      // pass them all up to your next step
      onUploadSuccess(
        tempPath,
        meaningfulBlock, allBlock,
        meaningfulLayer, allLayer,
        res.data.entity_types
      );
    } catch (err) {
      console.error(err);
      setMessage('Upload failed — check console.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20, border: '1px solid #ddd', borderRadius: 6 }}>
      <h3>Step 1: Upload DXF</h3>

      <div style={{ marginBottom: 12 }}>
        <label>Project ID *</label><br/>
        <input
          value={projectId}
          onChange={e => setProjectId(e.target.value)}
          disabled={loading}
          style={{ width: '100%', padding: '6px' }}
        />
      </div>

      <div style={{ marginBottom: 12 }}>
        <label>DXF File(s) *</label><br/>
        <input
          type="file"
          multiple
          accept=".dxf"
          onChange={handleFileChange}
          disabled={loading}
        />
      </div>

      {files.length > 0 && (
        <ul style={{ paddingLeft: 20 }}>
          {files.map((f, i) => (
            <li key={i} style={{ marginBottom: 4 }}>
              {f.name} ({(f.size / 1024).toFixed(1)} KB)
              <button
                onClick={() => removeFile(i)}
                disabled={loading}
                style={{
                  marginLeft: 8,
                  cursor: 'pointer',
                  border: 'none',
                  background: 'transparent',
                  color: '#900',
                  fontWeight: 'bold'
                }}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}

      <button
        onClick={handleUpload}
        disabled={loading}
        style={{
          marginTop: 12,
          padding: '10px 20px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: 4,
          cursor: 'pointer'
        }}
      >
        {loading ? 'Uploading…' : 'Upload DXF'}
      </button>

      {message && <p style={{ marginTop: 12 }}>{message}</p>}
    </div>
  );
};

export default DXFUploadForm;
