#pip install imageio
"""
Compiles batch-processed maximum wind speed maps into a chronological 
animated GIF to show regional climate changes over time.
"""

import os
import glob
import re

try:
    import imageio.v3 as iio
except ImportError:
    print("This script requires the 'imageio' library.")
    print("Please install it by running: pip install imageio")
    exit(1)

def create_wind_speed_gif():
    input_dir = 'output'
    gif_filename = 'conus_max_wind_speed_1980_2024.gif'
    
    # 1. Gather all matching PNG files from the output folder
    png_pattern = os.path.join(input_dir, 'max_wind_speed_conus_*.png')
    png_files = glob.glob(png_pattern)
    
    if not png_files:
        print(f"❌ No PNG files found matching pattern: {png_pattern}")
        print("Please ensure your batch processing script has run successfully first.")
        return

    # 2. Critical Sorting Logic: Extract the 4-digit year to sort chronologically.
    # Without this, files might load out of order (e.g., 1989 before 1980 depending on the OS).
    def extract_year(filepath):
        filename = os.path.basename(filepath)
        match = re.search(r'conus_(\d{4})\.png', filename)
        return int(match.group(1)) if match else 0

    png_files.sort(key=extract_year)
    
    print(f"Found {len(png_files)} frames. Compiling into an animated GIF...")

    # 3. Read each frame sequentially
    frames = []
    for filepath in png_files:
        year = extract_year(filepath)
        print(f"  Reading frame for year: {year}")
        try:
            img = iio.imread(filepath)
            frames.append(img)
        except Exception as e:
            print(f"  ❌ Error reading {filepath}: {e}")

    if not frames:
        print("❌ No valid frames were loaded. GIF creation aborted.")
        return

    # 4. Write out the final animated GIF
    # duration=500 means each year stays on screen for 500 milliseconds (0.5 seconds)
    # loop=0 makes the slideshow repeat infinitely
    print(f"\nWriting GIF to {gif_filename}...")
    try:
        iio.imwrite(gif_filename, frames, duration=500, loop=0)
        print(f"\n✓ Animated GIF successfully created: {gif_filename}")
    except Exception as e:
        print(f"❌ Error writing GIF: {e}")

if __name__ == '__main__':
    create_wind_speed_gif()