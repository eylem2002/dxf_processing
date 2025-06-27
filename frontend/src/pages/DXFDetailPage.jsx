import React from 'react';
import { useParams } from 'react-router-dom';
import DXFDetail from '../components/DXFDetail';

const DXFDetailPage = () => {
  const { id } = useParams();
  return <DXFDetail planId={id} />;
};

export default DXFDetailPage;
