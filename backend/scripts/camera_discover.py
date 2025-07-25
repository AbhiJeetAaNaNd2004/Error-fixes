import cv2
import sys
import argparse
from onvif import ONVIFCamera
from wsdiscovery import WSDiscovery

# Adjust import path to work from the 'backend' root directory
# To run this script, you must be in the 'backend' folder.
from db import db_utils

def discover_onvif_cameras():
    """Scans the local network for ONVIF-compliant cameras."""
    print("Scanning for ONVIF cameras on the network...")
    wsd = WSDiscovery()
    wsd.start()
    services = wsd.searchServices()
    wsd.stop()

    if not services:
        print("\nNo ONVIF devices were found on your LAN.")
        return

    print("\nDiscovered ONVIF devices:")
    print("-" * 30)
    for i, service in enumerate(services):
        try:
            # The getXAddrs() method returns a list of addresses.
            # We parse the first one to get the IP.
            ip_address = service.getXAddrs()[0].split('/')[2].split(':')[0]
            print(f"Device {i+1}:")
            print(f"  -> IP Address: {ip_address}")
            print(f"  -> Use this IP to construct the RTSP 'stream_url' when adding the camera to the database.")
        except IndexError:
            print(f"Device {i+1}: Found device but could not parse its address.")
    print("-" * 30)
    print("Note: You will still need to know the camera's full RTSP path, username, and password to add it to the database.")

def discover_local_cameras():
    """
    Scans for locally connected cameras (like USB webcams) and adds them
    to the database if they don't already exist.
    """
    print("\nScanning for local system cameras...")
    index = 0
    found_any = False
    while index < 10: # Check the first 10 device indices
        # Using CAP_DSHOW can be more stable on Windows
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            found_any = True
            stream_url = str(index)
            if not db_utils.camera_exists(stream_url):
                print(f"  -> New local camera found at index {index}. Adding to database...")
                # Add the camera with some default settings
                cam_id = db_utils.add_camera(
                    name=f"Local Camera {index}",
                    cam_type="entry", # Default type
                    stream_url=stream_url,
                    res_w=640,
                    res_h=480,
                    fps=15,
                    gpu_id=0 # Default GPU
                )
                if cam_id:
                    print(f"  -> Camera added with ID: {cam_id}")
                    # Optionally, add a default tripwire for the new camera
                    db_utils.add_tripwire(
                        camera_id=cam_id,
                        name=f"AutoTripwire_{index}",
                        direction="horizontal",
                        position=0.5,
                        spacing=0.01
                    )
            else:
                print(f"  -> Known local camera already exists at index {index}.")
            cap.release()
        index += 1

    if not found_any:
        print("-> No local system cameras were found.")

if __name__ == "__main__":
    # This is the same argument parsing logic from your original file
    parser = argparse.ArgumentParser(
        description="Camera Discovery Tool.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--scan',
        nargs='?',
        const='all',
        default='all', # Changed default to 'all' to be more intuitive
        choices=['local', 'lan', 'all'],
        help='''The type of camera scan to perform.
Options:
  local     - Scan for local system cameras only (e.g., USB webcams).
  lan       - Scan for LAN (ONVIF) cameras only.
  all       - (Default) Scan for both local and LAN cameras.'''
    )
    args = parser.parse_args()

    scan_mode = args.scan
    if scan_mode == 'all':
        print("--- Starting Camera Discovery (LAN & Local) ---")
        discover_onvif_cameras()
        discover_local_cameras()
    elif scan_mode == 'lan':
        print("--- Starting Camera Discovery (LAN only) ---")
        discover_onvif_cameras()
    elif scan_mode == 'local':
        print("--- Starting Camera Discovery (Local only) ---")
        discover_local_cameras()

    sys.exit(0)
