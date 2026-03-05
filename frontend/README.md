# AI Codebase Explainer - Frontend Dashboard

A modern Next.js frontend for analyzing GitHub repositories and exploring architecture insights with interactive Q&A.

## Features

- 🔍 **Repository Analysis** - Analyze any GitHub repository
- 📊 **Architecture Diagrams** - Visualize system architecture with Mermaid
- 🤖 **AI-Powered Q&A** - Ask questions about repository architecture
- 🎨 **Clean UI** - Built with React and Tailwind CSS
- ⚡ **Fast Performance** - Next.js optimized for speed
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

## Tech Stack

- **Framework**: Next.js 14
- **UI Library**: React 18
- **Styling**: Tailwind CSS
- **Diagrams**: Mermaid.js
- **HTTP Client**: Axios
- **Language**: JavaScript

## Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (see backend README)

## Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local if your backend API is on a different URL
   ```

## Running Locally

### Development Mode

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── pages/
│   ├── _app.js           # Next.js app wrapper
│   └── index.js          # Main dashboard page
├── components/
│   ├── RepositoryInput.js      # Input field for repo URL
│   ├── AnalysisSummary.js      # Display analysis results
│   ├── ArchitectureDiagram.js  # Render Mermaid diagrams
│   └── QuestionInput.js        # Q&A interface
├── lib/
│   └── api.js            # Axios API client
├── styles/
│   └── globals.css       # Global styles + Tailwind
├── public/               # Static assets
├── package.json          # Dependencies
├── next.config.js        # Next.js configuration
├── tailwind.config.js    # Tailwind configuration
└── postcss.config.js     # PostCSS configuration
```

## How It Works

### 1. Repository Analysis Flow

```
User enters GitHub URL
    ↓
POST /api/analyze
    ↓
Display metadata, frameworks, architecture
    ↓
Fetch diagram with GET /api/diagrams/{repo_name}
    ↓
Render Mermaid diagram
```

### 2. Architecture Q&A Flow

```
User types question
    ↓
Click "Ask" button
    ↓
POST /api/query
    ↓
Display answer with source info
```

## Components

### RepositoryInput
- Input field for GitHub URLs
- Submit button with loading state
- URL validation

### AnalysisSummary
- Display repository metadata
- Show primary language, file count
- List detected frameworks with confidence
- Show architecture patterns
- Display technology stack
- Show AI analysis (if available)

### ArchitectureDiagram
- Initialize Mermaid.js
- Render SVG diagram
- Handle loading and error states
- Scrollable for large diagrams

### QuestionInput
- Question input field
- Suggested question buttons
- Loading indicator
- Display answer results
- Show answer mode (AI or rule-based)

## API Integration

The frontend communicates with the backend API using the `api.js` client:

```javascript
import { analyzeRepository, getDiagram, queryArchitecture } from '../lib/api'

// Analyze a repository
const result = await analyzeRepository('https://github.com/owner/repo')

// Get diagram
const diagram = await getDiagram('repo-name', 'mermaid')

// Ask a question
const answer = await queryArchitecture('repo-name', 'What is this?')
```

## Mermaid Integration

The frontend uses Mermaid.js to render architecture diagrams:

1. Fetch diagram content from backend
2. Create a div with class "mermaid"
3. Set div content to diagram text
4. Call `mermaid.contentLoaded()`
5. Diagram renders automatically

```javascript
const svg = document.createElement('div')
svg.className = 'mermaid'
svg.textContent = diagramContent
container.appendChild(svg)
mermaid.contentLoaded()
```

## Features & Components

### Loading States
- Spinner during analysis
- Spinner during Q&A
- Skeleton loaders for diagrams

### Error Handling
- Display backend errors
- API connection status
- Graceful fallbacks

### Responsive Design
- Mobile-first approach
- Tailwind CSS breakpoints
- Flexible grid layouts

### Accessibility
- Semantic HTML
- Form labels
- ARIA attributes
- Keyboard navigation

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

This URL is used for all API requests. Change it if your backend is running on a different URL.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development Tips

### Hot Reload
The development server supports hot module reloading. Changes to files are instantly reflected.

### API Testing
Test API responses using the browser DevTools Network tab.

### Mermaid Syntax
Refer to [Mermaid documentation](https://mermaid.js.org/) for diagram syntax.

### Tailwind Classes
Refer to [Tailwind CSS documentation](https://tailwindcss.com/docs) for styling.

## Troubleshooting

### "API Unreachable"
- Ensure backend is running on the configured URL
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify CORS settings in backend

### Diagram Not Rendering
- Check browser console for errors
- Verify Mermaid syntax in backend response
- Try different diagram format

### Slow Performance
- Check Network tab for slow API requests
- Enable production mode
- Use CDN for static assets

## Build & Deployment

### Vercel (Recommended)

```bash
# Push to GitHub, then import in Vercel dashboard
# Or use Vercel CLI:
npm i -g vercel
vercel
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Traditional Server

```bash
npm run build
npm start
```

Visit `http://your-domain:3000`

## Contributing

Contributions welcome! Follow these guidelines:

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## License

MIT License - Feel free to use and modify

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review component documentation
3. Check backend API logs
4. Open an issue on GitHub

## Next Steps

- Add caching layer
- Implement bookmarks/favorites
- Add export to PDF
- Dark mode support
- Multi-language support
- Advanced filtering
- Performance analytics
