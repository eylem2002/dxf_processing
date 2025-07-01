/**
 * DXFUploadForm.jsx
 * 
 * A React component for uploading DXF files and linking them to a project.
 * 
 * Features:
 * - Form for entering project ID and optional filter parameters.
 * - Uploads multiple DXF files (prevents duplicates).
 * - Sends files and processing parameters to a FastAPI backend.
 * - Handles backend response and links floor plans to the project.
 * - Displays upload progress and status messages.
 * 
 * Accessibility: Includes labels, aria attributes, and keyboard-friendly controls.
 */

import React, { useState } from 'react';
import axios from 'axios';
import './DXFUploadForm.css';


/**
 * DXFUploadForm Component
 * 
 * Props:
 * - projectId: The current project ID (string)
 * - setProjectId: Function to update the project ID state in parent
 * - onUploadSuccess: Callback when upload & linking succeed
 */
const DXFUploadForm = ({ projectId, setProjectId, onUploadSuccess }) => {
  // Internal component state
  const [files, setFiles] = useState([]);
  const [dpi, setDpi] = useState('300');
  const [keywords, setKeywords] = useState('');
  const [blacklist, setBlacklist] = useState('');
  const [excludedLayers, setExcludedLayers] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  /**
   * handleFileChange
   * Prevents duplicate file selection and updates state with new files
   */
  const handleFileChange = (e) => {
    const selected = Array.from(e.target.files).filter(
      newFile => !files.some(existingFile => existingFile.name === newFile.name)
    );
    setFiles(prev => [...prev, ...selected]);
    e.target.value = null; // reset to allow selecting same file again if removed
  };

  /**
   * removeFile
   * Removes a selected file from the list by its index
   */
  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  /**
   * handleUpload
   * Validates input, sends files and processing parameters to backend,
   * links floor plans to the project, and handles upload state.
   */
  const handleUpload = async () => {
    // Validate mandatory fields: Project ID and Files
    if (!projectId.trim()) {
      alert("Project ID is required.");
      return;
    }
    if (files.length === 0) {
      alert("Please select at least one DXF file.");
      return;
    }

    setLoading(true);
    setMessage('Uploading, please wait...');

    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const params = {
      dpi: dpi || 300,
      keywords: keywords || undefined,
      blacklist: blacklist || undefined,
      excluded_layer_names: excludedLayers || undefined,
    };

    try {
      // Post DXF files and params to backend
      const res = await axios.post('http://localhost:8000/process_dxf/', formData, {
        params,
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Link returned floor plan IDs to project
      const planIds = res.data.floor_plan_ids || [];
      for (let id of planIds) {
        await axios.post('/link_dxf_to_project/', {
          project_id: projectId,
          floor_plan_id: id
        });
      }

      setMessage('Upload and linking successful.');
      setFiles([]); // Clear selected files after success
      onUploadSuccess(planIds);
    } catch (err) {
      console.error(err);
      setMessage('Upload failed. Please check console or backend logs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-form-container" role="form" aria-label="DXF Upload Form">
      <h3>Upload DXF Files</h3>

      {/* Inform user about mandatory fields */}
      <p className="info-text">
        Fields marked with <span className="required-star">*</span> are required.  
        All others are optional. You must provide Project ID and select at least one DXF file.
      </p>

      <div className="form-group">
        <label htmlFor="projectIdInput">
          Project ID <span className="required-star">*</span>
        </label>
        <input
          id="projectIdInput"
          type="text"
          value={projectId}
          onChange={e => setProjectId(e.target.value)}
          disabled={loading}
          placeholder="Enter project ID"
          autoComplete="off"
          aria-required="true"
        />
      </div>

      <div className="form-group">
        <label htmlFor="dpiInput">DPI (default 300)</label>
        <input
          id="dpiInput"
          type="number"
          value={dpi}
          onChange={e => setDpi(e.target.value)}
          disabled={loading}
          min="50"
          max="1200"
          aria-required="false"
        />
      </div>

      <div className="form-group">
        <label htmlFor="keywordsInput">Keywords (comma-separated)</label>
        <input
          id="keywordsInput"
          type="text"
          value={keywords}
          onChange={e => setKeywords(e.target.value)}
          disabled={loading}
          placeholder="e.g. FIRST, GROUND"
          aria-required="false"
        />
      </div>

      <div className="form-group">
        <label htmlFor="blacklistInput">Blacklist (comma-separated)</label>
        <input
          id="blacklistInput"
          type="text"
          value={blacklist}
          onChange={e => setBlacklist(e.target.value)}
          disabled={loading}
          placeholder="e.g. TAG, LEVEL, ALL"
          aria-required="false"
        />
      </div>

      <div className="form-group">
        <label htmlFor="excludedLayersInput">Excluded Layers (comma-separated)</label>
        <input
          id="excludedLayersInput"
          type="text"
          value={excludedLayers}
          onChange={e => setExcludedLayers(e.target.value)}
          disabled={loading}
          placeholder="e.g. A-ANNOTATION, A-ROOF_02"
          aria-required="false"
        />
      </div>

      <div className="form-group">
        <label htmlFor="fileInput">
          Select DXF Files <span className="required-star">*</span>
        </label>
        <input
          id="fileInput"
          type="file"
          multiple
          accept=".dxf"
          onChange={handleFileChange}
          disabled={loading}
          aria-required="true"
        />
      </div>

      {/* Show selected files with remove option */}
      {files.length > 0 && (
        <div className="selected-files">
          <p><strong>Selected Files ({files.length}):</strong></p>
          <ul>
            {files.map((file, index) => (
              <li key={index} className="file-item">
                {file.name} ({(file.size / 1024).toFixed(1)} KB)
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  disabled={loading}
                  aria-label={`Remove file ${file.name}`}
                  className="remove-file-btn"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        className="upload-btn"
        onClick={handleUpload}
        disabled={loading}
        aria-busy={loading}
      >
        {loading ? 'Uploading...' : 'Upload DXF'}
      </button>

      {message && (
        <p
          className={`feedback ${message.includes('failed') ? 'error' : 'success'}`}
          role="alert"
          aria-live="polite"
        >
          {message}
        </p>
      )}
    </div>
  );
};

export default DXFUploadForm;
