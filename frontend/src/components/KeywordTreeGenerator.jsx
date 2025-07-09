import React, { useState } from 'react';
import axios from 'axios';

const ENTITY_TYPES = [
  'LINE',
  'LWPOLYLINE',
  'POLYLINE',
  'CIRCLE',
  'ARC',
  'ELLIPSE',
  'SPLINE',
  'TEXT',
  'HATCH',
  '3DSOLID',
];

const KeywordTreeGenerator = ({
  tempPath,
  projectId,
  blockKeywords = [],
  layerKeywords = [],
  onComplete
}) => {
  const [step, setStep] = useState(1);
  const [selectedKeywords, setSelectedKeywords] = useState([]);
  const [dpi, setDpi] = useState(300);
  const [selectedEntities, setSelectedEntities] = useState(new Set(ENTITY_TYPES));
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const [previewId, setPreviewId] = useState(null);
  const [imageUrls, setImageUrls] = useState([]);
  const [relPaths, setRelPaths] = useState([]);
  const [selectedImages, setSelectedImages] = useState(new Set());

  const [lightbox, setLightbox] = useState({ open: false, url: '', title: '' });

  const toggleKeyword = kw =>
    setSelectedKeywords(prev =>
      prev.includes(kw) ? prev.filter(x => x !== kw) : [...prev, kw]
    );

  const toggleEntity = type =>
    setSelectedEntities(prev => {
      const nxt = new Set(prev);
      nxt.has(type) ? nxt.delete(type) : nxt.add(type);
      return nxt;
    });

  const handleGenerate = async () => {
    if (!selectedKeywords.length) {
      alert('Select at least one keyword.');
      return;
    }
    setLoading(true);
    setMessage('Generating preview…');
    try {
      const res = await axios.post('/preview_from_selection/', {
        temp_path: tempPath,
        dpi,
        keywords: selectedKeywords,
        entity_types: Array.from(selectedEntities),
      });
      setPreviewId(res.data.preview_id);
      setImageUrls(res.data.image_urls);
      setRelPaths(res.data.image_urls.map(u => u.replace(/^\/static\//, '')));
      setStep(2);
      setMessage('');
    } catch (err) {
      console.error(err);
      setMessage('Failed to generate preview — check console.');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!selectedImages.size) {
      alert('Select at least one image to export.');
      return;
    }
    setLoading(true);
    setMessage('Exporting selected…');
    try {
      const res = await axios.post('/store_from_selection/', {
        preview_id: previewId,
        project_id: projectId,
        selected_paths: Array.from(selectedImages)
      });
      onComplete(res.data.floor_plan_id);
    } catch (err) {
      console.error(err);
      setMessage('Export failed — check console.');
    } finally {
      setLoading(false);
    }
  };

  const openLightbox = (url, rel) => {
    const title = (rel.split('/').pop() || '')
      .replace(/[-.]/g, ' ')
      .replace(/png$/i, '')
      .trim();
    setLightbox({ open: true, url, title });
  };
  const closeLightbox = () => setLightbox(lb => ({ ...lb, open: false }));

  return (
    <div style={{ padding: 20, border: '1px solid #ccc', borderRadius: 6 }}>
      <h3>Step 2: Select Keywords & Generate Preview</h3>

      <div>
        <label>DPI:</label><br />
        <input
          type="number"
          value={dpi}
          onChange={e => setDpi(+e.target.value)}
          disabled={loading}
          style={{ width: 80 }}
        />
      </div>

      <div style={{ margin: '12px 0' }}>
        <h4>Include Geometry Types</h4>
        {ENTITY_TYPES.map(type => (
          <label key={type} style={{ marginRight: 8 }}>
            <input
              type="checkbox"
              checked={selectedEntities.has(type)}
              onChange={() => toggleEntity(type)}
              disabled={loading}
            />{' '}
            {type}
          </label>
        ))}
      </div>

      {/* Keyword buttons */}
      <div style={{ margin: '20px 0' }}>
        <h4>Block Keywords</h4>
        {blockKeywords.length === 0 ? (
          <em>None found in blocks.</em>
        ) : (
          blockKeywords.map(kw => (
            <button
              key={`blk-${kw}`}
              onClick={() => toggleKeyword(kw)}
              disabled={loading}
              style={{
                margin: 4,
                padding: '6px 12px',
                background: selectedKeywords.includes(kw) ? '#d4ffd4' : '#f0f0f0',
                border: selectedKeywords.includes(kw) ? '2px solid green' : '1px solid #999',
                borderRadius: 4
              }}
            >
              {kw}
            </button>
          ))
        )}

        <h4 style={{ marginTop: 16 }}>Layer Keywords</h4>
        {layerKeywords.length === 0 ? (
          <em>None found in layers.</em>
        ) : (
          layerKeywords.map(kw => (
            <button
              key={`lay-${kw}`}
              onClick={() => toggleKeyword(kw)}
              disabled={loading}
              style={{
                margin: 4,
                padding: '6px 12px',
                background: selectedKeywords.includes(kw) ? '#d4ffd4' : '#f0f0f0',
                border: selectedKeywords.includes(kw) ? '2px solid green' : '1px solid #999',
                borderRadius: 4
              }}
            >
              {kw}
            </button>
          ))
        )}
      </div>

      <button onClick={handleGenerate} disabled={loading || !selectedKeywords.length}>
        {loading ? 'Generating…' : 'Generate Preview'}
      </button>
      {message && <p>{message}</p>}

      {step === 2 && (
        <>
          <h3 style={{ marginTop: 30 }}>Preview Images</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
            {imageUrls.map((url, idx) => {
              const rel = relPaths[idx];
              const isSel = selectedImages.has(rel);
              const title = (rel.split('/').pop() || '')
                .replace(/[-.]/g, ' ')
                .replace(/png$/i, '')
                .trim();
              return (
                <div key={rel} style={{ width: 260, cursor: 'pointer', textAlign: 'center' }}>
                  <div
                    onClick={() => openLightbox(url, rel)}
                    style={{ marginBottom: 8, fontWeight: 'bold' }}
                  >
                    {title}
                  </div>
                  <img
                    src={url}
                    alt={title}
                    width={240}
                    onClick={() => {
                      setSelectedImages(s => {
                        const nxt = new Set(s);
                        nxt.has(rel) ? nxt.delete(rel) : nxt.add(rel);
                        return nxt;
                      });
                    }}
                    style={{ borderRadius: 4, border: isSel ? '3px solid #007bff' : '1px solid #ccc' }}
                  />
                  <div style={{ marginTop: 4 }}>
                    <input type="checkbox" checked={isSel} readOnly /> Select
                  </div>
                </div>
              );
            })}
          </div>

          <button
            onClick={handleExport}
            disabled={loading || !selectedImages.size}
            style={{ marginTop: 20 }}
          >
            {loading ? 'Exporting…' : 'Export Selected'}
          </button>
        </>
      )}

      {lightbox.open && (
        <div
          onClick={closeLightbox}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{ position: 'relative', background: '#fff', padding: 20, borderRadius: 6 }}
          >
            <button
              onClick={closeLightbox}
              style={{
                position: 'absolute',
                top: 10,
                right: 10,
                fontSize: 18,
                background: 'transparent',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              ×
            </button>
            <img
              src={lightbox.url}
              alt={lightbox.title}
              style={{ maxWidth: '100%', maxHeight: '80vh', borderRadius: 4 }}
            />
            <div style={{ marginTop: 12, fontWeight: 'bold', textAlign: 'center' }}>
              {lightbox.title}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KeywordTreeGenerator;
