import os, sys, pygame
import json
from pygame.math import Vector2
import json


PIXELS_TO_M = 0.05

ASSET_DIR = os.path.join(os.path.dirname(__file__), "imgs")

def load_image(name):
    path = os.path.join(ASSET_DIR, name)
    if not os.path.exists(path):
        print(f"Missing asset: {path}")
        sys.exit(1)
    return pygame.image.load(path).convert_alpha()


def pxs_to_kph(v_px_s):
    return v_px_s * PIXELS_TO_M * 3.6

def pxs_to_mph(v_px_s):
    return pxs_to_kph(v_px_s) * 0.621371

def clamp(v, a, b):
    return max(a, min(b, v))

def snap_to_road(x, y, mask, radius=40, step=4):
    w, h = mask.get_width(), mask.get_height()
    try:
        px = mask.get_at((int(x), int(y)))
        if (px.r + px.g + px.b) > 700:
            return int(x), int(y)
    except Exception:
        pass
    for r in range(0, radius+1, step):
        for dx in range(-r, r+1, step):
            dy = r
            for sx, sy in ((dx, dy), (dx, -dy)):
                nx, ny = int(x + sx), int(y + sy)
                if 0 <= nx < w and 0 <= ny < h:
                    try:
                        p = mask.get_at((nx, ny))
                        if (p.r + p.g + p.b) > 700:
                            return nx, ny
                    except Exception:
                        pass
    return None

class WaypointRecorder:
    def __init__(self):
        self.record_interval = 0.5   # seconds between samples (0.5 or 1.0)
        self.time_since_last = 0.0
        self.recording = False
        self.waypoints = []
        self.save_path = None  # saved next to your main.py

    def start(self):
        print("🎥 Recording started!")
        self.recording = True
        self.waypoints = []  # reset old data

    def stop(self):
        print("🛑 Recording stopped!")
        self.recording = False
        self.save()  # auto-save on stop

    def update(self, dt, car_pos):
        if not self.recording:
            return

        self.time_since_last += dt

        # Only record when the time interval passes
        if self.time_since_last >= self.record_interval:
            self.waypoints.append((float(car_pos.x), float(car_pos.y)))
            self.time_since_last = 0.0

    def save(self):
        
        try:
            with open(self.save_path, "w") as f:
                json.dump(self.waypoints, f, indent=4)
            print(f"✅ Saved {len(self.waypoints)} waypoints to: {self.save_path}")
        except Exception as e:
            print("❌ Failed to save waypoints:", e)

    def compress_waypoints(input_file, output_file, step=5, smooth=True):
        """Take raw recorded waypoints [[x,y], ...] and compress them."""

        if not os.path.exists(input_file):
            print("No waypoint file found.")
            return

        # --- Load raw data ---
        with open(input_file, "r") as f:
            raw = json.load(f)

        print(f"Loaded {len(raw)} raw waypoints.")

        # --- Round coordinates ---
        rounded = [[round(p[0]), round(p[1])] for p in raw]

        # --- Downsample (every Nth point) ---
        down = rounded[::step]

        print(f"After downsampling (step={step}): {len(down)} waypoints remain.")

        # --- Smooth the path slightly ---
        if smooth and len(down) > 3:
            smoothed = []
            for i in range(len(down)):
                x = (down[i-1][0] + down[i][0] + down[(i+1) % len(down)][0]) / 3
                y = (down[i-1][1] + down[i][1] + down[(i+1) % len(down)][1]) / 3
                smoothed.append([round(x), round(y)])
            final_data = smoothed
        else:
            final_data = down

        # --- Save it ---
        with open(output_file, "w") as f:
            json.dump(final_data, f)

        print(f"Saved {len(final_data)} processed waypoints → {output_file}")

