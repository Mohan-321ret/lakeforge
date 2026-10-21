# Lakeforge Frontend - Setup Guide

## Project Structure

```
frontend/
├── index.html              # HTML entry point
├── package.json            # Dependencies and scripts
├── vite.config.js          # Vite configuration
├── .env                    # Environment variables (local)
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore patterns
└── src/
    ├── main.jsx            # React entry point
    ├── App.jsx             # Main app component
    ├── App.css             # App styles
    ├── index.css           # Base styles
    ├── components/
    │   ├── Navbar.jsx      # Navigation component
    │   └── Navbar.css      # Navbar styles
    ├── pages/
    │   ├── Dashboard.jsx   # Dashboard page ✅
    │   ├── Dashboard.css   # Dashboard styles
    │   ├── Inspector.jsx   # Data inspection page
    │   ├── QA.jsx          # Q&A page
    │   ├── Reports.jsx     # Reports page
    │   └── Settings.jsx    # Settings/source management
    ├── services/
    │   └── api.js          # API client
    └── hooks/
        └── useInspection.js # React hook for inspection state
```

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

This will install:
- React 18
- React Router v6 (for navigation)
- Vite (build tool and dev server)

### 2. Configure Environment

The `.env` file is already created with:
```
VITE_API_URL=http://localhost:8000/api
```

If your backend is running on a different port/host, update this URL.

### 3. Start Development Server

```bash
npm run dev
```

This starts Vite dev server on `http://localhost:5173`

Features:
- ✅ Hot module reloading (changes update instantly)
- ✅ Fast rebuild times
- ✅ Automatic browser refresh

### 4. Build for Production

```bash
npm run build
```

Creates optimized build in `dist/` folder:
- Minified code
- Optimized assets
- Source maps

### 5. Preview Production Build

```bash
npm run preview
```

Test the production build locally before deploying.

## Project Dependencies

### Production Dependencies
- **react** (18.2.0) - UI library
- **react-dom** (18.2.0) - React DOM rendering
- **react-router-dom** (6.20.0) - Client-side routing

### Development Dependencies
- **vite** (5.0.0) - Build tool and dev server
- **@vitejs/plugin-react** (4.2.0) - React support in Vite
- **tailwindcss** (3.4.0) - CSS framework (optional, not configured yet)
- **eslint** + **eslint-plugin-react** - Code linting

## Available Scripts

```bash
# Start development server (hot reload)
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Run ESLint (code quality check)
npm run lint
```

## Environment Variables

Vite uses `VITE_` prefix for environment variables (not `REACT_APP_`).

**Variables:**
- `VITE_API_URL` - Backend API URL (default: http://localhost:8000/api)

**Using in code:**
```javascript
// Use import.meta.env
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
```

## Architecture

### Component Structure
```
App (Router)
├── Navbar (All pages)
└── Routes
    ├── / → Dashboard
    ├── /inspect → Inspector
    ├── /qa → Q&A
    ├── /reports → Reports
    └── /settings → Settings
```

### State Management
- **Component State**: useState for local component state
- **Custom Hooks**: useInspection hook for inspection state
- **API Client**: Centralized api.js service

Future: Consider Redux/Context API for complex shared state

### API Communication
```
React Components
    ↓
api.js (ApiClient class)
    ↓
Backend (FastAPI)
    ↓
Database/External Services
```

## Styling

### CSS Files
- `index.css` - Global base styles
- `App.css` - App-level styles
- `components/*.css` - Component-specific styles
- `pages/*.css` - Page-specific styles

### CSS Classes
All components use CSS class naming:
- `.dashboard` - Dashboard container
- `.navbar` - Navbar container
- `.stat-card` - Stat card component
- `.source-card` - Source card component

See CSS files for detailed styling.

## Common Issues & Solutions

### Issue: npm install fails

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Try again
npm install
```

### Issue: Port 5173 already in use

**Solution:**
The dev server will automatically try a different port. Check the console output for the actual URL.

Or change port in `vite.config.js`:
```javascript
server: {
  port: 5174,  // Different port
}
```

### Issue: CORS errors in browser console

**Solution:**
Make sure backend is running and has CORS enabled:
- Backend should be running on http://localhost:8000
- Check `.env` file has correct `VITE_API_URL`
- Backend must have CORS middleware enabled (it does by default)

### Issue: "Cannot find module" errors

**Solution:**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Issue: Hot reload not working

**Solution:**
- Make sure you're accessing via `http://localhost:5173` (not 127.0.0.1)
- Check that browser supports ES modules
- Restart dev server: Ctrl+C, then `npm run dev`

## Browser Support

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

Vite with React 18 requires modern JavaScript support (ES2020+).

## Development Tips

### 1. Using React DevTools
Install React DevTools browser extension for easier debugging:
- Chrome: [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools)
- Firefox: [React Developer Tools](https://addons.mozilla.org/firefox/addon/react-devtools/)

### 2. Browser DevTools
- Press F12 to open DevTools
- Check Console for errors
- Use Network tab to debug API calls
- Use Application tab to check local storage

### 3. React Hooks Best Practices
- Always call hooks at the top level of components
- Use custom hooks to share stateful logic
- Keep component state simple; use API client for data

### 4. Component Organization
```
Component
├── Imports
├── Props validation (if using TypeScript later)
├── State (useState)
├── Effects (useEffect)
├── Event handlers
└── JSX render
```

## Deployment

### Deploy to Vercel (Recommended)
```bash
npm install -g vercel
vercel
```

### Deploy to Netlify
```bash
npm run build
# Upload dist/ folder to Netlify
```

### Deploy to Static Hosting
```bash
npm run build
# Upload dist/ folder to any static hosting service
```

## Next Steps

1. **Start dev server**: `npm run dev`
2. **Open http://localhost:5173** in browser
3. **Make sure backend is running** on http://localhost:8000
4. **Explore dashboard**: Add sources, test connections
5. **Build new features**: Follow component structure above
6. **Check console for errors**: F12 → Console tab

## Resources

- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [React Router Documentation](https://reactrouter.com/)
- [JavaScript ES6+ Guide](https://javascript.info/)

## Getting Help

- Check browser console (F12) for error messages
- Look at network requests (DevTools → Network tab)
- Check if backend is running on correct port
- Verify `.env` file has correct API URL
- Check `/src/services/api.js` for available API methods

---

**Ready to start?**

1. Install dependencies: `npm install`
2. Make sure backend is running
3. Start dev server: `npm run dev`
4. Open http://localhost:5173

🚀 Happy coding!
