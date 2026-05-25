"use client";

import Webcam from "react-webcam";
import { useRef, useState } from "react";
import { Sidebar } from "../components/Sidebar";

interface PredictionResult {
  type: string;
  category: string;
  type_confidence: number;
  category_confidence: number;
}

const webcamVideoConstraints: MediaTrackConstraints = {
  facingMode: { ideal: "environment" },
  width: { ideal: 1280 },
  height: { ideal: 720 },
};

export default function ScanPage() {
  const webcamRef = useRef<Webcam>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [mode, setMode] = useState<"webcam" | "upload">("webcam");
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function predictImage(imageBlob: Blob) {
    setLoading(true);
    setError(null);

    try {
      const fd = new FormData();
      fd.append("file", imageBlob, "image.jpg");

      const res = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        body: fd,
      });

      if (!res.ok) {
        throw new Error("Prediction failed");
      }

      const data: PredictionResult = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  async function detectWebcam() {
    const img = webcamRef.current?.getScreenshot();
    if (!img) {
      setError("Camera is not ready yet");
      return;
    }

    try {
      const { blob, preview } = await createCenteredWebcamCrop(img);
      setCapturedImage(preview);
      await predictImage(blob);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not capture webcam image");
    }
  }

  function handleImageUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const base64 = event.target?.result as string;
      setUploadedImage(base64);
      setCapturedImage(null);
      setResult(null);
      setError(null);
    };
    reader.readAsDataURL(file);
  }

  async function detectUpload() {
    if (!uploadedImage) return;

    const blob = await fetch(uploadedImage).then((r) => r.blob());
    await predictImage(blob);
  }

  function clearUpload() {
    setUploadedImage(null);
    setCapturedImage(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function switchMode(nextMode: "webcam" | "upload") {
    setMode(nextMode);
    setResult(null);
    setError(null);
    setCapturedImage(null);
    if (nextMode === "webcam") {
      setUploadedImage(null);
    }
  }

  return (
    <main className="eco-shell">
      <Sidebar active="scan" />

      <section className="dashboard-surface scan-surface">
        <div className="mountain-layer layer-back" />
        <div className="mountain-layer layer-front" />

        <div className="scan-workspace">
          <header className="dashboard-header">
            <p>SCAN & IDENTIFY</p>
            <h1>Identify trash</h1>
            <span>Use your webcam or upload an image to show the trash type and category.</span>
          </header>

          <div className="mode-switch" aria-label="Scan mode">
            <button
              className={mode === "webcam" ? "selected" : ""}
              onClick={() => switchMode("webcam")}
              type="button"
            >
              📷 Webcam
            </button>
            <button
              className={mode === "upload" ? "selected" : ""}
              onClick={() => switchMode("upload")}
              type="button"
            >
              📤 Upload
            </button>
          </div>

          <section className="scan-panel">
            <div className="capture-card">
              {mode === "webcam" ? (
                <>
                  <div className="camera-frame">
                    <Webcam
                      ref={webcamRef}
                      audio={false}
                      forceScreenshotSourceSize
                      screenshotQuality={0.95}
                      screenshotFormat="image/jpeg"
                      videoConstraints={webcamVideoConstraints}
                      className="camera-preview"
                    />
                    <span className="camera-guide" aria-hidden="true" />
                  </div>
                  <button
                    className="primary-action"
                    onClick={detectWebcam}
                    disabled={loading}
                    type="button"
                  >
                    {loading ? "Analyzing..." : "⌖ Detect Trash"}
                  </button>
                  {capturedImage && (
                    <div className="webcam-shot-preview">
                      <img src={capturedImage} alt="Last analyzed webcam frame" />
                      <span>Last analyzed frame</span>
                    </div>
                  )}
                </>
              ) : (
                <>
                  {!uploadedImage ? (
                    <button
                      className="upload-drop"
                      onClick={() => fileInputRef.current?.click()}
                      type="button"
                    >
                      <span>📁</span>
                      <strong>Upload image</strong>
                      <small>PNG, JPG, JPEG</small>
                    </button>
                  ) : (
                    <div className="upload-preview">
                      <img src={uploadedImage} alt="Uploaded trash preview" />
                    </div>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden-input"
                  />
                  <div className="action-row">
                    <button
                      className="primary-action"
                      onClick={detectUpload}
                      disabled={loading || !uploadedImage}
                      type="button"
                    >
                      {loading ? "Analyzing..." : "⌖ Detect Trash"}
                    </button>
                    <button
                      className="secondary-action"
                      onClick={clearUpload}
                      disabled={loading}
                      type="button"
                    >
                      Clear
                    </button>
                  </div>
                </>
              )}
            </div>

            <aside className="result-card" aria-live="polite">
              <h2>♻️ Result</h2>
              {error && <p className="error-message">Error: {error}</p>}

              {result ? (
                <div className="result-grid">
                  <ResultItem
                    label="TYPE OF TRASH"
                    icon="🧩"
                    value={result.type}
                    confidence={result.type_confidence}
                  />
                  <ResultItem
                    label="CATEGORY"
                    icon="🗂️"
                    value={result.category}
                    confidence={result.category_confidence}
                  />
                </div>
              ) : (
                <div className="empty-result">
                  <span>📸</span>
                  <p>Scan or upload an item to see its trash type and category.</p>
                </div>
              )}
            </aside>
          </section>
        </div>
      </section>
    </main>
  );
}

async function createCenteredWebcamCrop(dataUrl: string) {
  const image = await loadImage(dataUrl);
  const minDim = Math.min(image.naturalWidth, image.naturalHeight);
  // Reduce detection area to 50% of the center to lessen the scanning zone
  const sourceSize = minDim * 0.5;
  const sourceX = (image.naturalWidth - sourceSize) / 2;
  const sourceY = (image.naturalHeight - sourceSize) / 2;
  const outputSize = 640;
  const canvas = document.createElement("canvas");
  canvas.width = outputSize;
  canvas.height = outputSize;

  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("Could not prepare webcam image");
  }

  context.drawImage(
    image,
    sourceX,
    sourceY,
    sourceSize,
    sourceSize,
    0,
    0,
    outputSize,
    outputSize,
  );

  const preview = canvas.toDataURL("image/jpeg", 0.95);
  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (value) => {
        if (value) {
          resolve(value);
        } else {
          reject(new Error("Could not capture webcam image"));
        }
      },
      "image/jpeg",
      0.95,
    );
  });

  return { blob, preview };
}

function loadImage(src: string) {
  return new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Could not read webcam image"));
    image.src = src;
  });
}

function ResultItem({
  label,
  icon,
  value,
  confidence,
}: {
  label: string;
  icon: string;
  value: string;
  confidence: number;
}) {
  const percent = Math.min(confidence * 100, 100);

  return (
    <article className="result-item">
      <p>{label}</p>
      <strong>
        <span>{icon}</span>
        {value}
      </strong>
      <small>Confidence: {percent.toFixed(1)}%</small>
      <div className="confidence-bar">
        <span style={{ width: `${percent}%` }} />
      </div>
    </article>
  );
}
