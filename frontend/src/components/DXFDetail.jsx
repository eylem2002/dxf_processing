import React, { useEffect, useState } from 'react';
import axios from 'axios';

const DXFDetail = ({ planId }) => {
  const [data, setData] = useState(null);

  useEffect(() => {
    axios.get(`/floors/${planId}`).then(res => setData(res.data));
  }, [planId]);

  const exportImage = (floor, view_index) => {
    axios.post('/export/', {
      floor_id: planId,
      floor,
      view_index
    }).then(res => {
      alert("Exported to: " + res.data.exported_path);
    });
  };

  if (!data) return <div>Loading...</div>;

  return (
    <div>
      <h3>Floor Plan: {data.keyword}</h3>
      {Object.entries(data.metadata).map(([floor, views]) => (
        <div key={floor}>
          <h4>{floor}</h4>
          <div style={{ display: 'flex', gap: '10px' }}>
            {views.map((path, index) => (
              <div key={index}>
                <img src={`/${path}`} alt="" width="150" />
                <button onClick={() => exportImage(floor, index)}>Export</button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default DXFDetail;
