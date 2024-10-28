import json

import random
import aiohttp
import asyncio
from PIL import Image
from io import BytesIO


def rgb_to_hex(rgb_color):
    return '#{:02X}{:02X}{:02X}'.format(rgb_color[0], rgb_color[1], rgb_color[2])

field = None

async def get_field_prepared():
    global field

    if not field:
        with open('bot/points3x/template_data.json', 'r') as file:
            squares = json.load(file)

        field =[{"coord": it["coord"], "color": it["color"]} for it in squares]

    return field

# Function to fetch an image
async def fetch_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=False) as response:
            if response.status == 200:
                return await response.read()  # Return image bytes
            else:
                print(f"Failed to fetch image, status code: {response.status}")
                return None


# Function to extract x and y from the coord (where x is always 100 to 999)
def extract_xy(coord):
    # Subtract 1 to undo the "+1" from the coordinate
    adjusted_coord = int(coord) - 1

    # Extract x and y based on the rule that x is always 3 digits (100-999)
    x = int(str(adjusted_coord)[-3:])  # Last 3 digits are x
    y = int(str(adjusted_coord)[:-3])  # The remaining digits are y

    return x, y


# Function to check pixel color discrepancies
def check_pixel_color(image, pixels_to_check):
    # Load the image into PIL
    img = Image.open(BytesIO(image))
    img = img.convert('RGB')  # Ensure image is in RGB format (no alpha)

    discrepancies = []

    for pixel in pixels_to_check:
        coord = pixel['coord']  # Get pixel coord as string
        expected_hex = pixel['color']  # Expected hex color from JSON

        # Extract the x and y coordinates using the fixed rule for x (100 to 999)
        x, y = extract_xy(coord)

        # Get the actual RGB color of the pixel at (x, y)
        actual_rgb = img.getpixel((x, y))

        # Convert the actual RGB color to a hex string
        actual_hex = rgb_to_hex(actual_rgb)

        # Compare actual hex with expected hex
        if actual_hex != expected_hex.upper():
            discrepancies.append({
                "coord": coord,
                "x": x,
                "y": y,
                "actual_color": actual_hex,
                "expected_color": expected_hex
            })

    return discrepancies


async def get_cords_and_color():
    # URL of the PNG image to fetch
    image_url = 'https://image.notpx.app/api/v2/image'  # Replace with actual URL

    global field

    # Fetch image asynchronously
    image_bytes = await fetch_image(image_url)

    if image_bytes is not None:

        await get_field_prepared()

        # Check if any pixels do not match their expected colors
        discrepancies = check_pixel_color(image_bytes, field)

        discrepancy = discrepancies[random.randint(0, len(discrepancies) - 1)]
        result = {
            "coord": discrepancy['coord'],
            "color": discrepancy['expected_color']
        }
        return result