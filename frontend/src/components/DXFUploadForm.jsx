import React, { useState } from 'react';
import axios from 'axios';
import './DXFUploadForm.css';

const DXFUploadForm = ({ onUploadSuccess }) => {
  const [files, setFiles] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [dpi, setDpi] = useState('300');
  const [keywords, setKeywords] = useState('');
  const [blacklist, setBlacklist] = useState('');
  const [excludedLayers, setExcludedLayers] = useState('');
  const [message, setMessage] = useState('');

  const handleUpload = async () => {
    if (!projectId.trim()) {
      alert("Project ID is required.");
      return;
    }
    if (files.length === 0) {
      alert("Please select at least one DXF file.");
      return;
    }
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    const params = {
      dpi: dpi || 300,
      keywords: keywords || undefined,
      blacklist: blacklist || undefined,
      excluded_layer_names: excludedLayers || undefined,
    };
    try {
      const res = await axios.post('http://localhost:8000/process_dxf/', formData, {
        params,
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const planIds = res.data.floor_plan_ids || [];
      for (let id of planIds) {
        await axios.post('/link_dxf_to_project/', {
          project_id: projectId,
          floor_plan_id: id
        });
      }
      setMessage('✅ Upload & linking successful!');
      onUploadSuccess();
    } catch (err) {
      console.error(err);
      setMessage('❌ Upload failed. Check console or backend logs.');
    }
  };

  return (
    <div className="upload-form-container">
      <h3>📐 Upload DXF Files</h3>

      <div className="form-group">
        <label>Project ID</label>
        <input type="text" value={projectId} onChange={e => setProjectId(e.target.value)} />
      </div>

      <div className="form-group">
        <label>DPI (default 300)</label>
        <input type="number" value={dpi} onChange={e => setDpi(e.target.value)} />
      </div>

      <div className="form-group">
        <label>Keywords (comma-separated)</label>
        <input type="text" value={keywords} onChange={e => setKeywords(e.target.value)} />
      </div>

      <div className="form-group">
        <label>Blacklist (comma-separated)</label>
        <input type="text" value={blacklist} onChange={e => setBlacklist(e.target.value)} />
      </div>

      <div className="form-group">
        <label>Excluded Layers (comma-separated)</label>
        <input type="text" value={excludedLayers} onChange={e => setExcludedLayers(e.target.value)} />
      </div>

      <div className="form-group">
        <label>Select DXF Files</label>
        <input type="file" multiple accept=".dxf" onChange={e => setFiles([...e.target.files])} />
      </div>

      <button className="upload-btn" onClick={handleUpload}>Upload DXF</button>

      {message && <p className="feedback">{message}</p>}
    </div>
  );
};

export default DXFUploadForm;
