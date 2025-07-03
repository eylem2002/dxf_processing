import React, { useEffect, useState } from 'react';
import axios from 'axios';

/**
 * DXFDetail Component
 *
 * Displays a saved floor plan in a card layout.
 * Clicking a thumbnail opens a modal where you can zoom in/out.
 * You can still select up to two images for export.
 */
const DXFDetail = ({ planId }) => {
  const [data, setData] = useState(null);
  const [selection, setSelection] = useState([]);
  const [lightbox, setLightbox] = useState({
    open: false,
    url: '',
    name: '',
    zoom: 1
  });

  useEffect(() => {
    if (!planId) return;
    axios.get(`/floors/${planId}`)
      .then(res => setData(res.data))
      .catch(console.error);
  }, [planId]);

  if (!data) return <div>Loading floor plan…</div>;

  const { keyword, created_at, metadata } = data;
  const shortId = planId.slice(0, 8);
  const formattedDate = new Date(created_at).toLocaleString();

  const extractName = relPath => {
    const raw = relPath.split('/').pop() || '';
    return raw.replace(/[-.]/g, ' ').replace(/png$/i, '').trim();
  };

  const toggleSelect = (floor, idx) => {
    setSelection(sel => {
      const exists = sel.find(s => s.floor === floor && s.index === idx);
      if (exists) return sel.filter(s => !(s.floor === floor && s.index === idx));
      if (sel.length >= 2) return sel;
      return [...sel, { floor, index: idx }];
    });
  };

  const exportSelected = () => {
    if (!selection.length) return alert('Select up to two images.');
    selection.forEach(({ floor, index }) => {
      axios.post('/export/', { floor_id: planId, floor, view_index: index })
        .then(res => alert(`Exported to:\n${res.data.exported_path}`))
        .catch(() => alert(`Export failed for ${floor} view ${index + 1}`));
    });
  };

  const openLightbox = (url, name) => {
    setLightbox({ open: true, url, name, zoom: 1 });
  };
  const closeLightbox = () => setLightbox(lb => ({ ...lb, open: false }));
  const zoomIn = () => setLightbox(lb => ({ ...lb, zoom: lb.zoom + 0.2 }));
  const zoomOut = () => setLightbox(lb => ({ ...lb, zoom: Math.max(0.2, lb.zoom - 0.2) }));

  return (
    <div style={{ maxWidth: 1000, margin: 'auto', fontFamily: 'Arial, sans-serif' }}>
      {/* Header */}
      <header style={{ textAlign: 'center', marginBottom: 40 }}>
        <h1>Floor Plan Detail</h1>
        <p>
          <strong>Plan ID:</strong> {shortId} &nbsp;|&nbsp;
          <strong>Primary:</strong> {keyword.toLowerCase()} &nbsp;|&nbsp;
          <strong>Created:</strong> {formattedDate}
        </p>
      </header>

      {/* Thumbnails */}
      {Object.entries(metadata).map(([floor, views]) => (
        <section key={floor} style={{ marginBottom: 50 }}>
          <h2 style={{ textTransform: 'capitalize', borderBottom: '2px solid #eee', paddingBottom: 8 }}>
            {floor.toLowerCase()}
          </h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            gap: 20,
            marginTop: 20
          }}>
            {views.map((relPath, idx) => {
              const url = `/static/${relPath}`;
              const name = extractName(relPath);
              const isSelected = !!selection.find(s => s.floor === floor && s.index === idx);

              return (
                <div key={idx} style={{
                  border: isSelected ? '3px solid #007bff' : '1px solid #ccc',
                  borderRadius: 8,
                  overflow: 'hidden',
                  background: '#fafafa',
                  boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
                  position: 'relative'
                }}>
                  <img
                    src={url}
                    alt={name}
                    style={{ width: '100%', display: 'block', cursor: 'zoom-in' }}
                    onClick={() => openLightbox(url, name)}
                  />
                  <div style={{ padding: '10px' }}>
                    <div style={{ fontWeight: 'bold', marginBottom: 6 }}>{name}</div>
                    <div style={{ fontSize: '0.85em', color: '#555' }}>{formattedDate}</div>
                    <label style={{ marginTop: 8, display: 'block', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        readOnly
                        style={{ marginRight: 6 }}
                        onClick={() => toggleSelect(floor, idx)}
                      />
                      Select
                    </label>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ))}

      {/* Export Button */}
      <div style={{ textAlign: 'center', marginBottom: 60 }}>
        <button
          onClick={exportSelected}
          disabled={!selection.length}
          style={{
            padding: '12px 30px',
            fontSize: 16,
            backgroundColor: selection.length ? '#007bff' : '#ccc',
            color: 'white',
            border: 'none',
            borderRadius: 6,
            cursor: selection.length ? 'pointer' : 'not-allowed'
          }}
        >
          Export Selected ({selection.length})
        </button>
      </div>

      {/* Lightbox Modal */}
      {lightbox.open && (
        <div
          onClick={closeLightbox}
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.8)',
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            zIndex: 1000, padding: 20
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{ position: 'relative', background: '#fff', padding: 10, borderRadius: 6 }}
          >
            {/* Close */}
            <button
              onClick={closeLightbox}
              style={{
                position: 'absolute', top: 8, right: 8,
                background: 'transparent', border: 'none', fontSize: 24, cursor: 'pointer'
              }}
            >×</button>

            {/* Image */}
            <img
              src={lightbox.url}
              alt={lightbox.name}
              style={{
                transform: `scale(${lightbox.zoom})`,
                transformOrigin: 'center center',
                maxWidth: '80vw',
                maxHeight: '80vh',
                display: 'block',
                margin: '0 auto'
              }}
            />

            {/* Controls */}
            <div style={{ textAlign: 'center', marginTop: 8 }}>
              <button onClick={zoomOut} style={controlStyle}>–</button>
              <span style={{ margin: '0 12px' }}>{(lightbox.zoom * 100).toFixed(0)}%</span>
              <button onClick={zoomIn} style={controlStyle}>+</button>
            </div>

            {/* Title */}
            <div style={{ textAlign: 'center', marginTop: 8, fontWeight: 'bold' }}>
              {lightbox.name}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// shared style for zoom buttons
const controlStyle = {
  width: 32,
  height: 32,
  fontSize: 20,
  backgroundColor: '#007bff',
  color: 'white',
  border: 'none',
  borderRadius: 4,
  cursor: 'pointer'
};

export default DXFDetail;
