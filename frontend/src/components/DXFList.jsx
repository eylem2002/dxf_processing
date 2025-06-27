/**
 * DXFList Component
 * ----------------------------------------------------------------------------
 * This component is responsible for displaying a list of processed DXF floor
 * plans that belong to a specific AIN360 project.
 * 
 * Key Responsibilities:
 * - Fetch floor plans associated with a given `projectId` from the backend API.
 * - Display each plan as a hyperlink to its detail page using React Router.
 * 
 * Assumptions:
 * - The backend exposes GET /projects/:projectId/dxfs to return DXF plan data.
 * - Each DXF plan includes `id` and `keyword` fields.
 */
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

/**
 * DXFList
 * ----------------------------------------------------------------------------
 * A functional React component that loads and renders a list of DXF floor plans.
 *
 * Props:
 * - projectId (string): The ID of the project whose DXF floor plans should be displayed.
 *   Required for the component to function properly.
 * 
 * Behavior:
 * - When `projectId` changes, the component fetches the corresponding DXF plans.
 * - Each returned plan is displayed as a clickable link using React Router.
 */
const DXFList = ({ projectId }) => {
  const [plans, setPlans] = useState([]);

  /**
   * useEffect Hook
   * ----------------------------------------------------------------------------
   * Triggers data fetching whenever the `projectId` changes.
   * 
   * - Prevents API call if `projectId` is undefined or empty.
   * - Sends GET request to `/projects/:projectId/dxfs`.
   * - On success: stores the list of plans in local state.
   * - On error: logs the error to the browser console.
   */

  useEffect(() => {
    if (!projectId) return; // prevent 404
    axios.get(`/projects/${projectId}/dxfs`)
      .then(res => setPlans(res.data))
      .catch(err => console.error(err));
  }, [projectId]);

  /**
   * JSX Return
   * ----------------------------------------------------------------------------
   * Renders an unordered list of DXF plans with hyperlinks to their detail pages.
   */
  
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
