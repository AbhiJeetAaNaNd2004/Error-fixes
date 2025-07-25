import asyncio
import base64
import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from typing import Optional, List, Dict

from dependencies import app_state 
from core.tracker import FaceTrackingSystem
from core.camera_manager import CameraManager
# UPDATED: Import the new WebSocket authentication function
from api.auth import get_current_user_from_cookie, TokenData 

router = APIRouter()

# --- Helper function for drawing annotations (no changes) ---
def draw_annotations(
    frame: np.ndarray, 
    tracking_data: Dict, 
    camera_config: Dict, 
    show_tripwires: bool,
    show_bboxes: bool = True
) -> np.ndarray:
    """Draws face boxes and optionally tripwires on a frame."""
    annotated_frame = frame.copy()
    
    # Draw face bounding boxes only if enabled
    if show_bboxes and tracking_data and tracking_data.get('identities'):
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

def get_camera_manager() -> CameraManager:
    camera_manager = app_state.get("camera_manager")
    if not camera_manager:
        raise RuntimeError("CameraManager not initialized")
    return camera_manager

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
    show_bboxes: bool = Query(True),  # NEW: Add bounding box toggle
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
            
        # FIXED: Dynamic frame rate calculation instead of hardcoded 0.03s
        camera_fps = camera_config.get('fps', 30)  # Default to 30 FPS if not specified
        frame_interval = 1.0 / camera_fps  # Calculate interval based on camera FPS
        max_fps = 30  # Limit maximum streaming FPS to prevent overwhelming clients
        min_interval = 1.0 / max_fps
        sleep_interval = max(frame_interval, min_interval)
        
        print(f"Camera {camera_id} streaming at {1/sleep_interval:.1f} FPS (camera FPS: {camera_fps})")
        
        while True:
            raw_frame = tracker.get_latest_raw_frame(camera_id)
            tracking_data = tracker.get_latest_tracking_data(camera_id)
            if raw_frame is not None:
                annotated_frame = draw_annotations(
                    raw_frame, 
                    tracking_data.__dict__ if tracking_data else {}, 
                    camera_config, 
                    show_tripwires,
                    show_bboxes  # Pass the bounding box toggle
                )
                ret, buffer = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                if ret:
                    frame_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
                    await websocket.send_text(frame_base64)
            await asyncio.sleep(sleep_interval)  # FIXED: Dynamic sleep interval
    except WebSocketDisconnect:
        print(f"Client '{user.username}' disconnected from camera {camera_id} feed.")
    except Exception as e:
        print(f"An unexpected error occurred for user '{user.username}' on camera {camera_id}: {e}")
    finally:
        manager.disconnect(websocket)

# NEW: Raw camera feed endpoint without face tracking
@router.websocket("/ws/raw_camera_feed/{camera_id}")
async def raw_camera_websocket_endpoint(
    websocket: WebSocket,
    camera_id: int,
    user: TokenData = Depends(get_current_user_from_cookie),
    camera_manager: CameraManager = Depends(get_camera_manager)
):
    """
    Protected WebSocket endpoint for raw camera feeds without face tracking.
    Allows viewing camera streams independently of the face recognition system.
    """
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or missing authentication cookie")
        return

    if user.role not in ["admin", "super_admin"]:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Insufficient permissions")
        return
        
    await manager.connect(websocket)
    print(f"User '{user.username}' (role: {user.role}) connected to raw camera {camera_id} feed.")
    
    try:
        # Ensure camera is running
        if not camera_manager.is_camera_running(camera_id):
            # Try to start the camera
            if not camera_manager.start_camera(camera_id):
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Failed to start camera")
                return
        
        # Get camera status for FPS information
        camera_status = camera_manager.get_camera_status(camera_id)
        if not camera_status:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Invalid camera ID")
            return
            
        # Calculate streaming parameters
        camera_fps = camera_status.get('configured_fps', 30)
        frame_interval = 1.0 / camera_fps
        max_fps = 30  # Limit maximum streaming FPS
        min_interval = 1.0 / max_fps
        sleep_interval = max(frame_interval, min_interval)
        
        print(f"Raw camera {camera_id} streaming at {1/sleep_interval:.1f} FPS (camera FPS: {camera_fps})")
        
        while True:
            raw_frame = camera_manager.get_camera_frame(camera_id)
            if raw_frame is not None:
                ret, buffer = cv2.imencode('.jpg', raw_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                if ret:
                    frame_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
                    await websocket.send_text(frame_base64)
            await asyncio.sleep(sleep_interval)
            
    except WebSocketDisconnect:
        print(f"Client '{user.username}' disconnected from raw camera {camera_id} feed.")
    except Exception as e:
        print(f"An unexpected error occurred for user '{user.username}' on raw camera {camera_id}: {e}")
    finally:
        manager.disconnect(websocket)

# NEW: Camera management endpoints
@router.get("/cameras/status")
async def get_all_cameras_status(
    user: TokenData = Depends(get_current_user_from_cookie),
    camera_manager: CameraManager = Depends(get_camera_manager)
):
    """Get status of all cameras."""
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    return camera_manager.get_all_camera_status()

@router.get("/cameras/{camera_id}/status")
async def get_camera_status(
    camera_id: int,
    user: TokenData = Depends(get_current_user_from_cookie),
    camera_manager: CameraManager = Depends(get_camera_manager)
):
    """Get status of a specific camera."""
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    status_info = camera_manager.get_camera_status(camera_id)
    if not status_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    
    return status_info

@router.post("/cameras/{camera_id}/start")
async def start_camera_stream(
    camera_id: int,
    user: TokenData = Depends(get_current_user_from_cookie),
    camera_manager: CameraManager = Depends(get_camera_manager)
):
    """Start a specific camera stream."""
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    success = camera_manager.start_camera(camera_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to start camera")
    
    return {"message": f"Camera {camera_id} started successfully"}

@router.post("/cameras/{camera_id}/stop")
async def stop_camera_stream(
    camera_id: int,
    user: TokenData = Depends(get_current_user_from_cookie),
    camera_manager: CameraManager = Depends(get_camera_manager)
):
    """Stop a specific camera stream."""
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    success = camera_manager.stop_camera(camera_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to stop camera")
    
    return {"message": f"Camera {camera_id} stopped successfully"}

@router.post("/cameras/start_all")
async def start_all_cameras(
    user: TokenData = Depends(get_current_user_from_cookie),
    camera_manager: CameraManager = Depends(get_camera_manager)
):
    """Start all configured cameras."""
    if user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")
    
    results = camera_manager.start_all_cameras()
    return {
        "message": f"Started {sum(results.values())} of {len(results)} cameras",
        "results": results
    }

@router.post("/cameras/stop_all")
async def stop_all_cameras(
    user: TokenData = Depends(get_current_user_from_cookie),
    camera_manager: CameraManager = Depends(get_camera_manager)
):
    """Stop all cameras."""
    if user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")
    
    results = camera_manager.stop_all_cameras()
    return {
        "message": f"Stopped {sum(results.values())} of {len(results)} cameras",
        "results": results
    }