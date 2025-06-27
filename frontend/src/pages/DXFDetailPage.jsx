// -----------------------------------------------------------------------------
// DXFDetailPage.jsx
//
// This page is responsible for displaying the detailed view of a single
// processed DXF file. It uses the plan ID extracted from the URL to load
// and render the corresponding floor plan details via the DXFDetail component.
//
// Route example: /dxf/:id
// -----------------------------------------------------------------------------

import React from 'react';
import { useParams } from 'react-router-dom';  // React Router hook to extract dynamic route parameters
import DXFDetail from '../components/DXFDetail';  // Component responsible for rendering DXF floor images and export options

/**
 * DXFDetailPage Component
 *
 * Retrieves the DXF `planId` from the URL using `useParams`,
 * then renders the `DXFDetail` component and passes the ID as a prop.
 * 
 * This page is typically rendered when the user clicks on a DXF entry
 * from the main list view, enabling them to interact with the floor data.
 */
const DXFDetailPage = () => {
  const { id } = useParams();  // Extracts `id` parameter from the route (e.g., /dxf/12345)
  
  // Render the DXF detail view for the given plan ID
  return <DXFDetail planId={id} />;
};

export default DXFDetailPage;
