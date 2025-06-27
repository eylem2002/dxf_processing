/**
 * DXFDetail Component
 *
 * A detailed view page for a single DXF floor plan.
 * - Fetches metadata for a specific floor plan using its `planId`.
 * - Renders all related floor images grouped by keyword (floor type).
 * - Allows the user to select an image and export it using the `/export/` API.
 *
 * Dependencies:
 * - React (hooks): useState, useEffect
 * - Axios: for communicating with the backend APIs
 */

import React, { useEffect, useState } from 'react';
import axios from 'axios';

/**
 * DXFDetail Component
 *
 * @param {string} planId - The unique identifier of the DXF floor plan to display
 * 
 * Functional Overview:
 * - Loads floor plan metadata on mount using planId.
 * - Displays image previews grouped by floor (keyword).
 * - Lets users select one image at a time.
 * - Sends export request for selected image via API.
 */
const DXFDetail = ({ planId }) => {

  // Stores the retrieved metadata for the floor plan
  const [data, setData] = useState(null);

  // Tracks the currently selected image (floor name + index)
  const [selectedImage, setSelectedImage] = useState({ floor: null, index: null });

  /**
   * Fetch floor plan metadata once planId is available.
   * Invoked automatically when component mounts or when planId changes.
   */
  useEffect(() => {
    if (!planId) return;
    axios.get(`/floors/${planId}`)
      .then(res => setData(res.data))
      .catch(err => console.error(err));
  }, [planId]);


  /**
   * Sends export request for the currently selected image.
   * Validates selection first and then hits `/export/` endpoint.
   */
  const exportImage = () => {
    if (!selectedImage.floor || selectedImage.index === null) {
      alert("Please select an image to export.");
      return;
    }

    axios.post('/export/', {
      floor_id: planId,
      floor: selectedImage.floor,
      view_index: selectedImage.index
    })
    .then(res => alert("Exported to: " + res.data.exported_path))
    .catch(err => {
      console.error(err);
      alert("Export failed.");
    });
  };

  // Show loading indicator while metadata is being fetched
  if (!data) return <div>Loading...</div>;

  return (
    <div style={{ maxWidth: '900px', margin: 'auto', fontFamily: 'Arial, sans-serif' }}>
      <h2 style={{ textAlign: 'center' }}>Floor Plan: {data.keyword}</h2>

      {Object.entries(data.metadata).map(([floor, views]) => (
        <div key={floor} style={{ marginBottom: '30px' }}>
          <h3>{floor}</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px' }}>
            {views.map((path, index) => {
              const isSelected = selectedImage.floor === floor && selectedImage.index === index;
              return (
                <div
                  key={index}
                  onClick={() => setSelectedImage({ floor, index })}
                  style={{
                    border: isSelected ? '3px solid #007bff' : '1px solid #ccc',
                    padding: '5px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    textAlign: 'center',
                    width: '160px'
                  }}
                >
                  <img src={`/static/${path}`} alt={`${floor} view ${index + 1}`} width="150" style={{ borderRadius: '4px' }} />
                  {isSelected && <div style={{ color: '#007bff', marginTop: '5px' }}>Selected</div>}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      <button
        onClick={exportImage}
        style={{
          backgroundColor: '#007bff',
          color: 'white',
          padding: '10px 20px',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
          display: 'block',
          margin: '20px auto',
          fontSize: '16px',
          opacity: selectedImage.floor ? 1 : 0.5,
          pointerEvents: selectedImage.floor ? 'auto' : 'none',
        }}
      >
        Export Selected Image
      </button>
    </div>
  );
};

export default DXFDetail;
