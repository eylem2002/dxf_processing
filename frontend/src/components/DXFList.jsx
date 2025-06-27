import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

const DXFList = ({ projectId }) => {
  const [plans, setPlans] = useState([]);

  useEffect(() => {
    if (!projectId) return; // prevent 404
    axios.get(`/projects/${projectId}/dxfs`)
      .then(res => setPlans(res.data))
      .catch(err => console.error(err));
  }, [projectId]);

  return (
    <ul>
      {plans.map(p => (
        <li key={p.id}>
          <Link to={`/dxfs/${p.id}`}>{p.keyword} ({p.id})</Link>
        </li>
      ))}
    </ul>
  );
};

export default DXFList;
