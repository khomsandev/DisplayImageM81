import React, { useState } from "react";
import ImageGallery from "./components/ImageGallery";

export default function App() {
  const [ids, setIds] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div style={{ padding: "24px", fontFamily: "sans-serif" }}>
      <h1>MFlow Image Viewer</h1>
      <p>ใส่หลาย <code>filesId</code> คั่นด้วยเครื่องหมายจุลภาค แล้วกด View</p>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={ids}
          onChange={(e) => setIds(e.target.value)}
          placeholder="uuid1,uuid2,uuid3"
          style={{
            width: "80%",
            padding: "8px 10px",
            borderRadius: "8px",
            border: "1px solid #ccc",
          }}
        />
        <button
          type="submit"
          style={{
            padding: "8px 14px",
            marginLeft: "8px",
            borderRadius: "8px",
            border: "none",
            background: "#333",
            color: "#fff",
            cursor: "pointer",
          }}
        >
          View
        </button>
      </form>

      {submitted && <ImageGallery ids={ids} />}
    </div>
  );
}
