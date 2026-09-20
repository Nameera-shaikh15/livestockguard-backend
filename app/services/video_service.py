import os
import tempfile
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from app.services.behaviour_service import behaviour_service


class VideoService:
    """
    Video Analysis Service.
    Uses OpenCV to extract frames and compute frame-differencing movement features.
    Delegates activity assessment to BehaviourService.
    
    IMPORTANT: Lightweight processing for hackathon requirements.
    Movement metrics are behavioural activity signals and NOT disease diagnoses.
    """

    def analyze_video(
        self,
        video_bytes: bytes,
        animal_id: str,
        species: str,
        target_frames: int = 12
    ) -> Dict[str, Any]:
        # Save video bytes to temporary file for OpenCV Cap
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        try:
            temp_file.write(video_bytes)
            temp_file.close()

            cap = cv2.VideoCapture(temp_file.name)
            if not cap.isOpened():
                return {
                    "frames_analyzed": 0,
                    "behaviour_indicators": [{
                        "modality": "video",
                        "name": "video_reading_error",
                        "confidence": 0.0,
                        "description": "Unable to open video stream for frame extraction."
                    }]
                }

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                total_frames = 30  # Fallback estimate if container metadata missing

            step = max(1, total_frames // target_frames)
            
            extracted_frames = []
            frame_idx = 0

            while cap.isOpened() and len(extracted_frames) < target_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, (320, 240))  # Downsample for lightweight computation
                extracted_frames.append(gray)
                frame_idx += step

            cap.release()

            if len(extracted_frames) < 2:
                # If single frame or static video
                indicators = behaviour_service.evaluate_activity_metrics(0.0, 0.9, len(extracted_frames))
                return {
                    "frames_analyzed": len(extracted_frames),
                    "behaviour_indicators": indicators
                }

            # Frame differencing analysis
            diffs = []
            stillness_count = 0
            for i in range(1, len(extracted_frames)):
                diff = cv2.absdiff(extracted_frames[i], extracted_frames[i - 1])
                mean_diff = float(np.mean(diff))
                diffs.append(mean_diff)
                if mean_diff < 3.5:  # Low movement threshold between frames
                    stillness_count += 1

            avg_frame_diff = float(np.mean(diffs)) if diffs else 0.0
            stillness_ratio = stillness_count / float(len(diffs)) if diffs else 0.0

            indicators = behaviour_service.evaluate_activity_metrics(
                mean_frame_diff=avg_frame_diff,
                stillness_ratio=stillness_ratio,
                frames_analyzed=len(extracted_frames)
            )

            return {
                "frames_analyzed": len(extracted_frames),
                "behaviour_indicators": indicators
            }
        finally:
            if os.path.exists(temp_file.name):
                try:
                    os.remove(temp_file.name)
                except Exception:
                    pass


video_service = VideoService()
