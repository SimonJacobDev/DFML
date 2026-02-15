import streamlit as st
import tempfile
from pathlib import Path
import requests

st.set_page_config(page_title="AI Deepfake Shield", layout="centered")

st.markdown("<h1 style='text-align:center;'>🛡️ AI Deepfake Shield</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:gray;'>Upload media like a social post — AI will verify authenticity</p>", unsafe_allow_html=True)

# ======================
# API SETTINGS
# ======================
default_api = "http://localhost:8000"
api_url = st.sidebar.text_input("API URL", value=default_api)
mode = st.radio("Post Type", ["Image", "Video"], horizontal=True)

file_types = ["jpg", "jpeg", "png"] if mode == "Image" else ["mp4", "mov", "avi"]
uploaded = st.file_uploader("Upload your media", type=file_types)

def save_tmp(uploaded_file):
    suffix = Path(uploaded_file.name).suffix
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(uploaded_file.getbuffer())
    tmp.flush()
    return tmp.name

# ======================
# UI START
# ======================
if uploaded:
    path = save_tmp(uploaded)

    st.markdown("### 📸 Post Preview")
    preview_placeholder = st.empty()

    if mode == "Image":
        preview_placeholder.image(path, use_column_width=True)
    else:
        preview_placeholder.video(path)

    # Auto detection
    with st.spinner("🔍 AI analyzing authenticity..."):
        endpoint = "/predict_image" if mode == "Image" else "/predict_video"
        url = api_url.rstrip("/") + endpoint

        files = {"file": open(path, "rb")}
        try:
            res = requests.post(url, files=files, timeout=120)
            res.raise_for_status()
            result = res.json()
        except Exception as e:
            st.error(f"API Error: {e}")
            st.stop()

    label = result.get("predicted_label", "unknown")
    confidence = float(result.get("confidence", 0))
    status = result.get("status", "safe")

    st.markdown("---")

    # ======================
    # SOCIAL BADGES
    # ======================
    if status == "safe":
        st.success(f"🟢 REAL Content (Confidence: {confidence:.2f})")
        color = "green"

    elif status == "suspicious":
        st.warning(f"🟡 Suspicious Content (Confidence: {confidence:.2f})")
        color = "orange"

    else:  # blocked
        st.error(f"🔴 FAKE Content Detected (Confidence: {confidence:.2f})")
        color = "red"

        # Blur overlay effect
        st.markdown(
            """
            <div style="
                background-color: rgba(255,0,0,0.1);
                padding: 10px;
                border-radius: 8px;
                margin-top:10px;">
                🚫 This media appears AI-manipulated and has been flagged.
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("📢 Report Deepfake"):
            st.success("Report submitted to moderation system!")

    # ======================
    # CONFIDENCE BAR
    # ======================
    st.markdown("### 🔎 Confidence Score")
    st.progress(min(int(confidence * 100), 100))
    st.markdown(f"<span style='color:{color}; font-weight:bold;'>{confidence*100:.1f}% Confidence</span>", unsafe_allow_html=True)

else:
    st.info("Upload an image or video to simulate a social media post.")
