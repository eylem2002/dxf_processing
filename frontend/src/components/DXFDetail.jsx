import React, { useEffect, useState } from 'react';
import axios from 'axios';

const DXFDetail = ({ planId }) => {
  const [data, setData] = useState(null);
  const [selectedImage, setSelectedImage] = useState({ floor: null, index: null });

  useEffect(() => {
    if (!planId) return;
    axios.get(`/floors/${planId}`)
      .then(res => setData(res.data))
      .catch(err => console.error(err));
  }, [planId]);

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
