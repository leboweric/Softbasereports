# Railway Build Optimization Guide

## Current Build Time: 10+ minutes → Target: 2-3 minutes

### Changes Made:

1. **Added .dockerignore** - Excludes frontend files, cache, docs from build
2. **Added nixpacks.toml** - Optimized build configuration for Railway
3. **Created requirements-fast.txt** - Minimal dependencies only

### Railway Dashboard Settings to Update:

1. **Go to Railway Project Settings**
2. **Environment Variables:**
   - Set `NIXPACKS_PYTHON_VERSION=3.11`
   
3. **Root Directory (if needed):**
   - Ensure it's pointing to repository root, not `reporting-backend`
   - The nixpacks.toml handles the directory navigation

### Optional Optimizations:

1. **Switch to requirements-fast.txt:**
   ```bash
   # In Railway settings, change build command to:
   cd reporting-backend && pip install -r requirements-fast.txt
   ```

2. **Remove unused dependencies:**
   - matplotlib (3.10.0) - 50MB+ 
   - seaborn (0.13.2) - 20MB+
   - scipy (1.13.1) - 30MB+
   - openai (1.59.8) - if not using AI features
   - reportlab (4.2.5) - if not generating PDFs

### Expected Results:
- **Build time**: 10+ min → 2-3 min
- **Image size**: Reduced by ~150MB
- **Deploy time**: Faster due to smaller image

### Testing:
After these changes, the next build should be significantly faster. If issues occur, revert by:
1. Removing nixpacks.toml
2. Using original requirements.txt