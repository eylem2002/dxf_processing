import React, { useEffect, useState } from 'react';
import axios from 'axios';

const DXFList = ({ projectId, onSelectPlan }) => {
  const [plans, setPlans] = useState([]);

  useEffect(() => {
    if (!projectId) return;
    axios.get(`/projects/${projectId}/dxfs`)
      .then(res => setPlans(res.data))
      .catch(console.error);
  }, [projectId]);

  return (
    <ul>
      {plans.map(p => (
        <li key={p.id}>
          <button
            style={{ background: 'none', border: 'none', color: '#07c', cursor: 'pointer' }}
            onClick={() => onSelectPlan(p.id)}
          >
            {p.keyword} — {p.id}
          </button>
        </li>
      ))}
    </ul>
  );
};

export default DXFList;
