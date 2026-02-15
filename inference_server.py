import torch
import cv2
import tempfile
import numpy as np
import librosa
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from transformers import (
    ViTForImageClassification,
    ViTImageProcessor,
    AutoFeatureExtractor,
    AutoModelForAudioClassification,
    AutoImageProcessor,
    AutoModelForImageClassification
)
import uvicorn
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

# ================= APP INIT =================
app = FastAPI(title="Deepfake Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_num_threads(2)
torch.set_grad_enabled(False)  # Disable gradients globally for speed

# ================= VIDEO MODEL =================
VIDEO_MODEL_NAME = "google/vit-base-patch16-224-in21k"
VIDEO_MODEL_PATH = "vit_deepfake_model.pth"

video_processor = ViTImageProcessor.from_pretrained(VIDEO_MODEL_NAME)
video_model = ViTForImageClassification.from_pretrained(VIDEO_MODEL_NAME, num_labels=2)
video_model.load_state_dict(torch.load(VIDEO_MODEL_PATH, map_location=device))
video_model.to(device).eval()

# ================= IMAGE MODEL =================

# ================= AUDIO MODEL =================
AUDIO_MODEL_NAME = "mo-thecreator/Deepfake-audio-detection"
audio_feature_extractor = AutoFeatureExtractor.from_pretrained(AUDIO_MODEL_NAME)
audio_model = AutoModelForAudioClassification.from_pretrained(AUDIO_MODEL_NAME)
audio_model.to(device).eval()
IMAGE_MODEL_NAME = "dima806/deepfake_vs_real_image_detection"

image_processor = None
image_model = None

def load_image_model():
    global image_processor, image_model
    if image_model is None:
        print("🔄 Loading image deepfake model...")
        image_processor = AutoImageProcessor.from_pretrained(IMAGE_MODEL_NAME)
        image_model = AutoModelForImageClassification.from_pretrained(IMAGE_MODEL_NAME)
        image_model.to(device)
        image_model.eval()

def load_image_model():
    global image_processor, image_model
    if image_model is None:
        print("🔄 Loading image deepfake model...")
        image_processor = AutoImageProcessor.from_pretrained(IMAGE_MODEL_NAME)
        image_model = AutoModelForImageClassification.from_pretrained(IMAGE_MODEL_NAME)
        image_model.to(device)
        image_model.eval()
# ---------------- VIDEO FRAME EXTRACTION ----------------
def extract_frames(video_path, num_frames=6):
    cap = cv2.VideoCapture(video_path)
    frames = []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total == 0:
        return []

    step = max(1, total // num_frames)
    for i in range(0, total, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (224, 224))
        frames.append(frame)
        if len(frames) >= num_frames:
            break
    cap.release()
    return frames

# ---------------- VIDEO PREDICTION ----------------
def predict_video_frames(frames):
    inputs = video_processor(images=frames, return_tensors="pt").to(device)
    outputs = video_model(**inputs).logits
    probs = torch.softmax(outputs, dim=1).cpu().numpy()
    mean_probs = probs.mean(axis=0)
    return {"real": float(mean_probs[0]), "fake": float(mean_probs[1])}, probs.tolist()

# ---------------- IMAGE ROUTE ----------------
@app.post("/predict_image")
async def predict_image(file: UploadFile = File(...)):
    load_image_model()  # 🚀 Load only when needed

    suffix = Path(file.filename).suffix or ".jpg"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        path = tmp.name

    img = cv2.imread(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    inputs = image_processor(images=img, return_tensors="pt").to(device)

    with torch.no_grad():
        logits = image_model(**inputs).logits
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

    labels = image_model.config.id2label
    pred_index = int(np.argmax(probs))
    predicted_label = labels[pred_index].lower()
    confidence = float(probs[pred_index])

    status = "fake" if "fake" in predicted_label else "real"

    return JSONResponse({
        "predicted_label": status,
        "confidence": confidence
    })

# ---------------- VIDEO ROUTE ----------------
@app.post("/predict_video")
async def predict_video(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        video_path = tmp.name

    frames = extract_frames(video_path)
    if not frames:
        return JSONResponse({"error": "Could not extract frames"}, status_code=400)

    mean_probs, frame_probs = predict_video_frames(frames)
    label = "fake" if mean_probs["fake"] > mean_probs["real"] else "real"

    return JSONResponse({
        "predicted_label": label,
        "mean_probabilities": mean_probs,
        "per_frame_probs": frame_probs
    })

# ---------------- AUDIO ROUTE ----------------
@app.post("/predict_audio")
async def predict_audio(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        audio_path = tmp.name

    speech, sr = librosa.load(audio_path, sr=16000, mono=True)
    speech = speech[:16000 * 5]  # limit to 5 sec

    inputs = audio_feature_extractor(speech, sampling_rate=16000, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    logits = audio_model(**inputs).logits
    probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

    labels = audio_model.config.id2label
    pred_index = int(np.argmax(probs))
    predicted_label = labels[pred_index].lower()
    confidence = float(probs[pred_index])

    status = "fake" if "fake" in predicted_label else "real"

    return JSONResponse({
        "predicted_label": status,
        "confidence": confidence
    })

if __name__ == "__main__":
    uvicorn.run("inference_server:app", host="0.0.0.0", port=8000)
