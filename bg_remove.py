import streamlit as st
from rembg import remove
from PIL import Image
from io import BytesIO
import os
import time
from pathlib import Path

# --- App Configuration ---
# Set page title, layout, and initial sidebar state
st.set_page_config(
    page_title="Image Background Remover",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- Constants ---
# Maximum allowed file size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
# Maximum dimension (width or height) for resizing images
MAX_DIMENSION = 2000  # pixels


# --- Utility Functions ---
def resize_image(image: Image.Image, max_dim: int) -> Image.Image:
    """
    Resize an image while preserving aspect ratio.

    Args:
        image: PIL Image to resize.
        max_dim: Maximum width or height.

    Returns:
        Resized PIL Image if larger than max_dim, else original.
    """
    w, h = image.size
    # If both dimensions are within limits, return original
    if max(w, h) <= max_dim:
        return image
    # Compute scaling factor based on larger dimension
    scale = max_dim / max(w, h)
    # Resize with high-quality Lanczos filter
    return image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


@st.cache_data(show_spinner=False)
def process_image(image_bytes: bytes) -> Image.Image:
    """
    Remove the background from image bytes using rembg.

    Args:
        image_bytes: Raw image data as bytes.

    Returns:
        PIL Image with transparent background.
    """
    # Open image and convert to RGBA (to include alpha channel)
    img = Image.open(BytesIO(image_bytes)).convert("RGBA")
    # Resize large images to speed up processing
    img = resize_image(img, MAX_DIMENSION)
    # Remove background
    result = remove(img)
    return result


# --- Sidebar: Upload & Settings ---
st.sidebar.title("Upload & Settings")
# File uploader for PNG/JPG images
upload = st.sidebar.file_uploader(
    "Choose an image (PNG/JPG)", type=["png", "jpg", "jpeg"]
)

# Option to fill transparent background with a solid color
fill_bg = st.sidebar.checkbox("Fill background with color", value=False)
if fill_bg:
    bg_color = st.sidebar.color_picker("Background fill color", "#FFFFFF")
else:
    bg_color = None

# --- Main Interface ---
st.title("🖼️ Image Background Remover")
st.write(
    "Upload an image to remove its background. You can optionally fill the transparent areas with a custom color."
)

if upload:
    # Check file size limit
    if hasattr(upload, "size") and upload.size > MAX_FILE_SIZE:
        st.sidebar.error(
            f"File too large: Max size is {MAX_FILE_SIZE // (1024*1024)} MB."
        )
    else:
        # Read image bytes from upload
        img_bytes = upload.read() if hasattr(upload, "read") else upload.getvalue()
        start = time.time()
        progress = st.sidebar.progress(0)
        status = st.sidebar.empty()

        # Update sidebar status and progress
        status.info("Processing...")
        progress.progress(20)
        # Remove background
        result = process_image(img_bytes)
        progress.progress(80)

        # If user wants to fill background, composite image over chosen color
        if fill_bg and bg_color:
            bg = Image.new("RGB", result.size, bg_color)
            bg.paste(result, mask=result.split()[3])
            final = bg
        else:
            final = result

        progress.progress(100)
        elapsed = time.time() - start
        status.success(f"Done in {elapsed:.2f}s")

        # Display original and processed images side by side
        col1, col2 = st.columns(2)
        col1.header("Original")
        col1.image(Image.open(BytesIO(img_bytes)), use_container_width=True)
        col2.header("Processed")
        col2.image(final, use_container_width=True)

        # Prepare download of processed image
        if final.mode == "RGBA":
            fmt, ext = "PNG", "png"
        else:
            fmt, ext = "JPEG", "jpg"
        download_name = f"processed_background_removed.{ext}"
        buf = BytesIO()
        final.save(buf, format=fmt)
        st.sidebar.download_button(
            "Download image",
            data=buf.getvalue(),
            file_name=download_name,
            mime=f"image/{ext}",
        )
else:
    # Prompt user to upload or select example
    st.info("👆 Upload an image or choose an example to get started!")
