"""
detector.py — target detection from a camera frame.

Given a BGR frame from camera.py, finds the largest blob of the target
color (HSV range defined in config.py) and returns its pixel center.

This is the second link in the tracking pipeline:
    camera → DETECTOR → tracker → servo

It is the ONLY module that contains the color-detection logic. If you
need to change how detection works (different color space, contour
filtering, ML-based detection, etc.), change it here — every caller
just sees `detect(frame) -> (x, y) | None`.

Public API:
    detect(frame)            → (x, y) pixel coords of target, or None
    build_mask(frame)        → binary mask (for debugging / tune_detector)

Algorithm (detect):
    1. Gaussian blur the BGR frame (5×5) — smooths sensor noise so small
       speckles don't fragment the target.
    2. Convert BGR → HSV. HSV separates hue (color) from value (brightness),
       which makes thresholding far more lighting-tolerant than RGB.
    3. cv2.inRange against config.HSV_LOWER/HSV_UPPER → binary mask.
    4. Erode then dilate (morphological opening) — kills isolated noise
       pixels but restores the size of the real blob.
    5. Find external contours. Pick the largest by area.
    6. Reject if the largest area is still below MIN_CONTOUR_AREA — that's
       background noise, not the target.
    7. Compute the centroid via image moments and return (cx, cy).
"""

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

import config

log = logging.getLogger(__name__)

# Structuring element for erode/dilate. None lets OpenCV use a default
# 3×3 kernel, which is the typical sweet spot for noise removal at
# this resolution.
_MORPH_KERNEL = None
_MORPH_ITERATIONS: int = 2

# Gaussian blur kernel size. Must be odd. 5×5 is gentle — enough to
# smooth sensor noise without losing edge sharpness.
_BLUR_KERNEL: Tuple[int, int] = (5, 5)


def build_mask(frame: np.ndarray) -> np.ndarray:
    """
    Apply the full pre-contour pipeline to a BGR frame and return the
    cleaned binary mask. Public so tune_detector.py and debugging
    callers can preview exactly what detect() sees.

    Pipeline: blur → BGR→HSV → inRange → erode → dilate.
    """
    blurred = cv2.GaussianBlur(frame, _BLUR_KERNEL, 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, config.HSV_LOWER, config.HSV_UPPER)
    mask = cv2.erode(mask, _MORPH_KERNEL, iterations=_MORPH_ITERATIONS)
    mask = cv2.dilate(mask, _MORPH_KERNEL, iterations=_MORPH_ITERATIONS)
    return mask


def detect(frame: np.ndarray) -> Optional[Tuple[int, int]]:
    """
    Find the target in a BGR frame.

    Returns (x, y) pixel coordinates of the target's center, or None if
    no contour large enough to be the target is found. The coordinates
    are in OpenCV image convention: x increases right, y increases DOWN
    from the top-left corner.

    The caller is expected to compare against (FRAME_CENTER_X,
    FRAME_CENTER_Y) to compute tracking error.
    """
    mask = build_mask(frame)

    # RETR_EXTERNAL: only outer contours, ignore holes inside the blob.
    # CHAIN_APPROX_SIMPLE: store only contour endpoints, not every pixel.
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < config.MIN_CONTOUR_AREA:
        # Largest blob is still too small — treat as noise, no target.
        return None

    # Image moments give us the centroid analytically without needing
    # to enumerate pixels. m00 = total mass (area), m10/m01 = first
    # moments → centroid = (m10/m00, m01/m00).
    moments = cv2.moments(largest)
    if moments["m00"] == 0:
        # Degenerate contour (zero area despite passing area check —
        # shouldn't happen, but guard against divide-by-zero anyway).
        return None

    cx = int(moments["m10"] / moments["m00"])
    cy = int(moments["m01"] / moments["m00"])
    return cx, cy
