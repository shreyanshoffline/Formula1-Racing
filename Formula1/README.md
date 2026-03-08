# Top-Down Racer - Single-file Pygame prototype
Author: Shreyansh

## What this prototype provides:
- Top-down car with arcade-but-physically-plausible movement
- Camera that follows the player's car (world -> screen transform)
- Large track image that represents the race course
- Simple off-track detection via a "track mask" image (road pixels marked)
- AI opponents that follow a list of waypoints
- Lap counting using a start/finish line rectangle
- Basic HUD (speed, lap, position)

## Assets you'll need (In same folder as this file):
- track.png           -> big image of the track (background)
- track_mask.png      -> same size as track.png; road pixels = white (255,255,255), off-road = black
- car_player.png      -> top-down car sprite pointing up (0 degrees)
- car_ai.png          -> AI car sprite (same orientation)

## Quick run:
1) Install pygame: pip install pygame
2) Put the assets in the folder
3) python TopDownRacer.py

## Description and Additional features from latest updates
- Realistic-ish longitudinal + lateral forces
- Throttle/brake ramping, steering smoothing
- Aero downforce, rolling resistance, aerodynamic drag
- Simple tire lateral model (slip damping)
- AI that follows normalized waypoints and uses throttle/steer controller
- Lap detection and minimap
-
> Note: Requires pygame, assets in imgs/ (Track_1.png, Track_1_mask.png, Mclaren.png, RedBull.png)
