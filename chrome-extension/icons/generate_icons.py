#!/usr/bin/env python3
"""
Simple icon generator for PatternShield Chrome Extension
Creates basic placeholder PNG icons
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_shield_icon(size, filename):
    """Create a simple shield icon with PatternShield colors"""
    
    # Create image with gradient-like color
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Calculate sizes
    padding = size // 8
    shield_width = size - (2 * padding)
    shield_height = size - (2 * padding)
    
    # Draw circle background
    draw.ellipse([padding, padding, size - padding, size - padding], 
                 fill=(102, 126, 234, 255))  # #667eea
    
    # Draw shield shape (simplified)
    shield_points = [
        (size // 2, padding + 5),  # Top
        (padding + 5, padding + shield_height // 4),  # Left
        (padding + 5, padding + shield_height // 2),  # Left middle
        (size // 2, size - padding - 5),  # Bottom
        (size - padding - 5, padding + shield_height // 2),  # Right middle
        (size - padding - 5, padding + shield_height // 4),  # Right
    ]
    
    draw.polygon(shield_points, fill=(255, 255, 255, 230))
    
    # Draw checkmark (simplified)
    check_size = size // 4
    check_x = size // 2
    check_y = size // 2
    
    # Checkmark lines
    if size >= 48:  # Only draw checkmark on larger icons
        line_width = max(2, size // 32)
        draw.line([
            (check_x - check_size // 2, check_y),
            (check_x - check_size // 4, check_y + check_size // 2)
        ], fill=(102, 126, 234, 255), width=line_width)
        draw.line([
            (check_x - check_size // 4, check_y + check_size // 2),
            (check_x + check_size // 2, check_y - check_size // 4)
        ], fill=(102, 126, 234, 255), width=line_width)
    
    # Save icon
    img.save(filename, 'PNG')
    print(f"Created {filename} ({size}x{size})")

def main():
    """Generate all required icon sizes"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    sizes = [
        (16, 'icon16.png'),
        (48, 'icon48.png'),
        (128, 'icon128.png')
    ]
    
    for size, filename in sizes:
        filepath = os.path.join(script_dir, filename)
        create_shield_icon(size, filepath)
    
    print("\n✓ All icons generated successfully!")
    print("Icons are basic placeholders. Consider creating professional icons for production.")

if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("Error: PIL (Pillow) not installed")
        print("Install with: pip install Pillow")
        print("\nAlternatively, create simple colored squares:")
        print("Or use an online tool: https://redketchup.io/icon-converter")
