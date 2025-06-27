// -----------------------------------------------------------------------------
// HomePage.jsx
//
// Main landing page of the DXF viewer application.
// Provides functionality to upload new DXF files and view existing ones,
// optionally filtered by a specific AIN360 project ID.
// -----------------------------------------------------------------------------

import React, { useState } from 'react';
import DXFUploadForm from '../components/DXFUploadForm'; // Form to handle DXF file uploads
import DXFList from '../components/DXFList';             // List of processed DXF entries

/**
 * HomePage Component
 *
 * Displays:
 *  - A title and instructions.
 *  - A form to upload DXF files and link them to a project.
 *  - A text input to filter files by Project ID.
 *  - A list of existing DXF records, optionally filtered by project.
 *
 * The `refresh` state triggers re-rendering the DXF list after a successful upload.
 * The `projectId` state synchronizes between the upload form and the filter input.
 */
const HomePage = () => {
  const [refresh, setRefresh] = useState(false);      // Trigger to reload DXF list
  const [projectId, setProjectId] = useState('');      // Holds the currently selected project ID

  return (
    <div
      style={{
        maxWidth: '700px',
        margin: 'auto',
        padding: '20px',
        fontFamily: 'Arial, sans-serif'
      }}
    >
      {/* Page title */}
      <h2 style={{ textAlign: 'center' }}>Upload & View DXF Files</h2>

      {/* Upload form: Allows submitting one or more DXF files */}
      {/* `onUploadSuccess` toggles refresh state to reload list after upload */}
      <DXFUploadForm
        projectId={projectId}
        setProjectId={setProjectId}
        onUploadSuccess={() => setRefresh(!refresh)}
      />

      {/* Filter input to show only DXFs linked to a specific project */}
      <div style={{ marginTop: '30px' }}>
        <label htmlFor="projectIdInput" style={{ fontWeight: 'bold' }}>
          Filter by Project ID:
        </label>
        <input
          id="projectIdInput"
          type="text"
          placeholder="Enter project ID"
          value={projectId}
          onChange={e => setProjectId(e.target.value)}
          style={{
            marginLeft: '10px',
            padding: '6px 10px',
            fontSize: '14px',
            borderRadius: '4px',
            border: '1px solid #ccc'
          }}
        />
      </div>

      {/* Display list of DXF files, filtered by project ID */}
      {/* Re-renders when `refresh` state changes */}
      <DXFList projectId={projectId} key={refresh} />
    </div>
  );
};

export default HomePage;
