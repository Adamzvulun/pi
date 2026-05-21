"""
camera.py — owner module for the camera subsystem.

The ONLY module that may import cv2 for camera capture. All other code
that needs frames calls capture_frame() here.

This implementation uses a USB webcam via cv2.VideoCapture. If a Pi CSI
camera is later connected, only this file changes — the public API is
identical so no downstream code needs updating.

Public API:
    init(width, height, device_index) → cv2.VideoCapture
    capture_frame(cap)                → numpy BGR array
    release(cap)                      → None
"""

import logging
from typing import Optional

import cv2
import numpy as np

log = logging.getLogger(__name__)


def init(width: int = 640, height: int = 480, device_index: int = 0) -> cv2.VideoCapture:
    """
    Open the USB webcam and configure it for the requested resolution.

    device_index=0 is correct when one webcam is plugged in. If multiple
    USB cameras are connected and you need a specific one, increment the index.

    The driver may not honor the exact resolution requested — most webcams
    will select the closest supported mode. The actual resolution is logged
    so you can verify.

    Raises:
        RuntimeError: camera could not be opened (check USB connection and
                      that no other process has it locked).
    """
    log.info("Opening webcam at device index %d (%dx%d)", device_index, width, height)
    cap = cv2.VideoCapture(device_index)

    if not cap.isOpened():
        raise RuntimeError(
            f"Cannot open camera at index {device_index}. "
            "Check that the USB webcam is plugged in and not in use by another process."
        )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # Read back actual resolution — log it so we can spot mismatches.
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    log.info("Camera opened: actual resolution %dx%d", actual_w, actual_h)

    return cap


def capture_frame(cap: cv2.VideoCapture) -> np.ndarray:
    """
    Capture one frame from the webcam. Returns it as a BGR numpy array,
    which is the format OpenCV expects for all subsequent processing.

    Unlike picamera2, VideoCapture already delivers BGR so no color-order
    conversion is needed here.

    Raises:
        RuntimeError: frame read failed (camera disconnected or driver error).
    """
    ret, frame = cap.read()
    if not ret or frame is None:
        raise RuntimeError(
            "Failed to read frame from webcam. "
            "Camera may have been disconnected or encountered a driver error."
        )
    return frame


def release(cap: cv2.VideoCapture) -> None:
    """
    Release the webcam and free OS resources.
    Always call this in a finally block.
    """
    log.info("Releasing webcam")
    cap.release()
