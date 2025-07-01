import React, { useEffect, useState } from 'react';
import axios from 'axios';

const KeywordTreeGenerator = ({ planId }) => {
  const [tree, setTree] = useState([]);                // raw keyword tree
  const [selectedKeywords, setSelectedKeywords] = useState([]);
  const [filteredViews, setFilteredViews] = useState(null);
  const [selectedImages, setSelectedImages] = useState([]);

  // 1) Load the tree from the new endpoint
  useEffect(() => {
    axios.get('/api/keywords/tree')
      .then(res => setTree(res.data.children || []))
      .catch(console.error);
  }, []);

  // Toggle a keyword checkbox
  const toggleKeyword = (kw) =>
    setSelectedKeywords(prev =>
      prev.includes(kw)
        ? prev.filter(x => x !== kw)
        : [...prev, kw]
    );

  // 2) “Generate” for those keywords: fetch the metadata, filter it, show images
  const generateImages = () => {
    axios.get(`/floors/${planId}`)
      .then(res => {
        const meta = res.data.metadata || {};
        const filtered = Object.fromEntries(
          Object.entries(meta).filter(([k]) => selectedKeywords.includes(k))
        );
        setFilteredViews(filtered);
        setSelectedImages([]);
      })
      .catch(console.error);
  };

  // Toggle an image in the gallery
  const toggleImage = (floor, idx) => {
    const id = `${floor}-${idx}`;
    setSelectedImages(prev =>
      prev.includes(id)
        ? prev.filter(x => x !== id)
        : [...prev, id]
    );
  };

  // 3) “Regenerate” = re-export all selected images
  const regenerate = () => {
    Promise.all(
      selectedImages.map(id => {
        const [floor, idx] = id.split('-');
        return axios.post('/export/', {
          floor_id: planId,
          floor,
          view_index: parseInt(idx, 10),
        });
      })
    )
    .then(() => alert('Exported all selected images!'))
    .catch(console.error);
  };

  return (
    <div style={{ maxWidth: 900, margin: 'auto', fontFamily: 'Arial, sans-serif' }}>
      <h2 style={{ textAlign: 'center' }}>Step 2: Select Keywords & Generate</h2>

      <div>
        {tree.map(node => (
          <label key={node.name} style={{ marginRight: 16 }}>
            <input
              type="checkbox"
              checked={selectedKeywords.includes(node.name)}
              onChange={() => toggleKeyword(node.name)}
            />
            {node.name}
          </label>
        ))}
      </div>

      <button
        onClick={generateImages}
        disabled={selectedKeywords.length === 0}
        style={{ margin: '20px 0', padding: '8px 20px', cursor: 'pointer' }}
      >
        Generate Images
      </button>

      {filteredViews && (
        <div>
          {Object.entries(filteredViews).map(([floor, views]) => (
            <div key={floor} style={{ marginBottom: 30 }}>
              <h3>{floor}</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 15 }}>
                {views.map((path, i) => {
                  const id = `${floor}-${i}`;
                  const selected = selectedImages.includes(id);
                  return (
                    <div
                      key={i}
                      onClick={() => toggleImage(floor, i)}
                      style={{
                        border: selected ? '3px solid #007bff' : '1px solid #ccc',
                        borderRadius: 6,
                        padding: 5,
                        cursor: 'pointer',
                        width: 160,
                        textAlign: 'center',
                      }}
                    >
                      <img
                        src={`/static/${path}`}
                        alt={`${floor} view ${i + 1}`}
                        width={150}
                        style={{ borderRadius: 4 }}
                      />
                      {selected && <div style={{ color: '#007bff', marginTop: 5 }}>Selected</div>}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          <button
            onClick={regenerate}
            disabled={selectedImages.length === 0}
            style={{ padding: '8px 20px', cursor: 'pointer' }}
          >
            Regenerate Selected
          </button>
        </div>
      )}
    </div>
  );
};

export default KeywordTreeGenerator;
