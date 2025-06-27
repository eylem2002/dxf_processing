import React, { useState } from 'react';
import axios from 'axios';

const DXFUploadForm = ({ onUploadSuccess }) => {
  const [files, setFiles] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [message, setMessage] = useState('');       
  const [isError, setIsError] = useState(false);     

  const handleUpload = async () => {
    if (!projectId.trim()) {
      setIsError(true);
      setMessage("Project ID is required.");
      return;
    }
    if (files.length === 0) {
      setIsError(true);
      setMessage("Please select at least one DXF file to upload.");
      return;
    }

    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    const params = { dpi: 300 };

    try {
      setMessage('Uploading... please wait.');
      setIsError(false);

      const res = await axios.post('http://localhost:8000/process_dxf/', formData, {
        params,
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const planIds = res.data.floor_plan_ids;

      for (let id of planIds) {
        await axios.post('/link_dxf_to_project/', {
          project_id: projectId,
          floor_plan_id: id
        });
      }

      setMessage('Upload successful!');
      setIsError(false);
      onUploadSuccess();
    } catch (err) {
      console.error(err);
      setMessage('Upload failed. Please try again.');
      setIsError(true);
    }
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Project ID"
        value={projectId}
        onChange={e => setProjectId(e.target.value)}
      />
      <input
        type="file"
        multiple
        onChange={e => setFiles([...e.target.files])}
      />
      <button onClick={handleUpload}>Upload DXF</button>
      {message && (
        <p style={{ color: isError ? 'red' : 'green', marginTop: '10px' }}>
          {message}
        </p>
      )}
    </div>
  );
};

export default DXFUploadForm;
