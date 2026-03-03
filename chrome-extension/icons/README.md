# PatternShield Extension Icons

## Placeholder Icons

The extension requires PNG icons in three sizes:
- icon16.png (16x16) - Toolbar icon
- icon48.png (48x48) - Extension management page
- icon128.png (128x128) - Chrome Web Store

## Quick Generation Method

### Option 1: Use Online Tool (Easiest)
1. Go to https://redketchup.io/icon-converter
2. Upload any image (logo, shield icon, etc.)
3. Select output sizes: 16x16, 48x48, 128x128
4. Download and rename to icon16.png, icon48.png, icon128.png

### Option 2: Use ImageMagick (CLI)
```bash
# If you have a source icon (icon.png or icon.svg)
convert icon.svg -resize 16x16 icon16.png
convert icon.svg -resize 48x48 icon48.png
convert icon.svg -resize 128x128 icon128.png
```

### Option 3: Use Python with PIL
```python
from PIL import Image

# Create a simple colored square (temporary)
for size in [16, 48, 128]:
    img = Image.new('RGB', (size, size), color='#667eea')
    img.save(f'icon{size}.png')
```

### Option 4: Use the provided generator script
```bash
# Run the icon generator (creates simple placeholder icons)
python3 generate_icons.py
```

## Temporary Placeholder

For testing, you can use simple colored squares. The extension will work fine with placeholder icons during development.

## Design Recommendations

For a professional look:
- Use a shield icon to represent "protection"
- Incorporate a checkmark or warning symbol
- Use the brand colors: #667eea (purple) and #764ba2 (darker purple)
- Keep design simple and recognizable at small sizes
- Ensure good contrast for visibility in both light and dark themes

## Icon Resources

Free icon sources:
- Flaticon: https://www.flaticon.com/
- Font Awesome: https://fontawesome.com/
- Heroicons: https://heroicons.com/
- Material Icons: https://fonts.google.com/icons
