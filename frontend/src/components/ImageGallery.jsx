import React, { useEffect, useState } from "react";

export default function ImageGallery({ ids }) {
  const [images, setImages] = useState([]);

  useEffect(() => {
    const fetchImages = async () => {
      const idList = ids.split(",").map((x) => x.trim()).filter(Boolean);
      setImages(idList);
    };
    fetchImages();
  }, [ids]);

  if (!images.length) return <p>ไม่พบข้อมูลภาพ</p>;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
        gap: "16px",
        marginTop: "20px",
      }}
    >
      {images.map((fid) => (
        <div
          key={fid}
          style={{
            border: "1px solid #e5e5e5",
            borderRadius: "8px",
            padding: "10px",
            background: "#fff",
          }}
        >
          <img
            src={`/api/img/${fid}`}
            alt={fid}
            style={{
              width: "100%",
              height: "200px",
              objectFit: "contain",
              background: "#fafafa",
              borderRadius: "8px",
            }}
            onError={(e) => {
              e.target.src =
                "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='200'><rect width='100%' height='100%' fill='%23f0f0f0'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='14'>Load error</text></svg>";
            }}
          />
          <div style={{ fontSize: "12px", color: "#666", marginTop: "8px" }}>
            {fid}
          </div>
        </div>
      ))}
    </div>
  );
}
