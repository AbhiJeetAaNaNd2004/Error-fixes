import asyncio
import base64
import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from typing import Optional, List, Dict

from dependencies import app_state 
from core.tracker import FaceTrackingSystem
# UPDATED: Import the new WebSocket authentication function
from api.auth import get_current_user_from_cookie, TokenData 

router = APIRouter()

# --- Helper function for drawing annotations (no changes) ---
def draw_annotations(
    frame: np.ndarray, 
    tracking_data: Dict, 
    camera_config: Dict, 
    show_tripwires: bool
) -> np.ndarray:
    """Draws face boxes and optionally tripwires on a frame."""
    annotated_frame = frame.copy()
    
    # Draw face bounding boxes
    if tracking_data and tracking_data.get('identities'):
        for identity, score, bbox in zip(tracking_data['identities'], tracking_data['scores'], tracking_data['bboxes']):
            x1, y1, x2, y2 = [int(i) for i in bbox]
            color = (0, 255, 0) if identity != "unknown" else (0, 0, 255)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            label = f"{identity} ({score:.2f})"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(annotated_frame, (x1, y1 - h - 10), (x1 + w, y1), color, -1)
            cv2.putText(annotated_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    # Draw tripwires if requested
    if show_tripwires and camera_config:
        frame_height, frame_width, _ = annotated_frame.shape
        for tripwire in camera_config.get('tripwires', []):
            color = (255, 0, 255)  # Magenta for tripwires
            if tripwire['direction'] == 'vertical':
                x = int(frame_width * tripwire['position'])
                cv2.line(annotated_frame, (x, 0), (x, frame_height), color, 2)
                cv2.putText(annotated_frame, tripwire['name'], (x + 5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            else:  # horizontal
                y = int(frame_height * tripwire['position'])
                cv2.line(annotated_frame, (0, y), (frame_width, y), color, 2)
                cv2.putText(annotated_frame, tripwire['name'], (10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
    return annotated_frame

def get_tracker() -> FaceTrackingSystem:
    tracker = app_state.get("tracker")
    if not tracker:
        raise RuntimeError("FaceTrackingSystem not initialized")
    return tracker

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

manager = ConnectionManager()

@router.websocket("/ws/video_feed/{camera_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    camera_id: int,
    # UPDATED: Use the new WebSocket-specific dependency
    user: TokenData = Depends(get_current_user_from_cookie),
    show_tripwires: bool = Query(False),
    tracker: FaceTrackingSystem = Depends(get_tracker)
):
    """
    Protected WebSocket endpoint. A valid httpOnly cookie must be present.
    Streams video feed with annotations. Access is restricted.
    """
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or missing authentication cookie")
        return

    if user.role not in ["admin", "super_admin"]:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Insufficient permissions")
        return
        
    await manager.connect(websocket)
    print(f"User '{user.username}' (role: {user.role}) connected to camera {camera_id} feed.")
    try:
        camera_config = tracker.get_camera_config(camera_id)
        if not camera_config:
            print(f"ERROR: User '{user.username}' requested invalid camera_id {camera_id}.")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Invalid camera ID")
            return
        while True:
            raw_frame = tracker.get_latest_raw_frame(camera_id)
            tracking_data = tracker.get_latest_tracking_data(camera_id)
            if raw_frame is not None:
                annotated_frame = draw_annotations(
                    raw_frame, 
                    tracking_data.__dict__ if tracking_data else {}, 
                    camera_config, 
                    show_tripwires
                )
                ret, buffer = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                if ret:
                    frame_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
                    await websocket.send_text(frame_base64)
            await asyncio.sleep(0.03)
    except WebSocketDisconnect:
        print(f"Client '{user.username}' disconnected from camera {camera_id} feed.")
    except Exception as e:
        print(f"An unexpected error occurred for user '{user.username}' on camera {camera_id}: {e}")
    finally:
        manager.disconnect(websocket)