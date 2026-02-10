# Company Logo Instructions

To add your company logo to the Bennett Business Intelligence system:

1. Place your company logo image file in the `/public` directory
2. Name it `bennett-logo.png` (or update the filename in Layout.jsx)
3. Recommended specifications:
   - Format: PNG with transparent background
   - Height: 40-60 pixels (will be auto-scaled)
   - Width: Auto (maintains aspect ratio)

The logo will appear in the upper left corner of the sidebar navigation.

If no logo is found, it will fall back to displaying "Bennett BI" as text.

To use a different filename or path, update these lines in Layout.jsx:
- Line 52: `src="/bennett-logo.png"`
- Line 126: `src="/bennett-logo.png"`