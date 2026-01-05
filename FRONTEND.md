# Frontend Development Guide

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js 14 app directory
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Home page
│   │   ├── providers.tsx # React Query provider
│   │   └── globals.css   # Global styles
│   ├── components/       # React components
│   │   ├── ChatInterface.tsx
│   │   ├── FolderManager.tsx
│   │   ├── PersonaCards.tsx
│   │   └── MemoryPanel.tsx
│   ├── lib/
│   │   └── api.ts        # API client functions
│   └── store/
│       └── chat.ts       # Zustand state management
├── public/               # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## Key Components

### ChatInterface

Main chat component with streaming support and source citations.

```tsx
<ChatInterface />
```

Features:
- Message history display
- Markdown rendering
- Thinking process expansion
- Source citations
- Real-time streaming

### FolderManager

Upload conversations from ChatGPT, Gemini, or manual transcripts.

```tsx
<FolderManager onClose={() => setShowFolderManager(false)} />
```

Features:
- File upload
- Source type selection
- Progress tracking
- Error handling

### PersonaCards

Display psychological profiles with Big Five traits.

```tsx
<PersonaCards />
```

Features:
- Persona list
- Trait visualization
- Core values display
- Goals and fears
- Conflict indicators

### MemoryPanel

Show memory tier usage and system status.

```tsx
<MemoryPanel />
```

Features:
- Memory tier visualization
- Active features status
- Statistics display
- Real-time updates

## State Management

Using Zustand for global state:

```tsx
import { useChatStore } from '@/store/chat'

function MyComponent() {
  const { messages, addMessage, isLoading } = useChatStore()
  
  // Use state...
}
```

## API Integration

All API calls in `src/lib/api.ts`:

```tsx
import { chat, ingest, profiles, memory } from '@/lib/api'

// Send chat message
const response = await chat.send("Hello", conversationId)

// Upload conversations
await ingest.upload({ file, source: 'chatgpt' })

// Get persona profile
const persona = await profiles.get("John Doe")

// Get memory stats
const stats = await memory.getStats()
```

## Styling

Using Tailwind CSS:

```tsx
<div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900">
  <h1 className="text-2xl font-bold">Title</h1>
</div>
```

Dark mode supported automatically with `dark:` variants.

## Data Fetching

Using React Query for server state:

```tsx
const { data, isLoading, error } = useQuery({
  queryKey: ['personas'],
  queryFn: () => profiles.list(),
  refetchInterval: 30000, // Refresh every 30s
})
```

## Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Development

```bash
# Run dev server
npm run dev

# Type check
npm run type-check

# Build for production
npm run build

# Run production build
npm start
```

## WebSocket (Future)

For real-time streaming:

```tsx
import { io } from 'socket.io-client'

const socket = io(process.env.NEXT_PUBLIC_WS_URL)

socket.on('chat_stream', (chunk) => {
  // Handle streaming chunks
})
```

## Testing (Future)

```bash
# Install test dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest

# Run tests
npm test
```

## Deployment

```bash
# Build
npm run build

# Deploy to Vercel
vercel deploy

# Or deploy to any static host
# The build output is in .next/
```

## Best Practices

1. **Components**: Keep components small and focused
2. **State**: Use Zustand for global state, React Query for server state
3. **Types**: Always define TypeScript interfaces
4. **Styles**: Use Tailwind utilities, avoid custom CSS
5. **API**: All API calls through centralized api.ts
6. **Performance**: Use React.memo for expensive components
7. **Accessibility**: Include ARIA labels and keyboard navigation

## Common Patterns

### Loading States

```tsx
{isLoading ? (
  <Loader2 className="w-5 h-5 animate-spin" />
) : (
  <Content />
)}
```

### Error Handling

```tsx
try {
  const result = await api.call()
} catch (error: any) {
  setError(error.response?.data?.detail || 'An error occurred')
}
```

### Conditional Rendering

```tsx
{messages.length === 0 ? (
  <EmptyState />
) : (
  messages.map(msg => <Message key={msg.id} {...msg} />)
)}
```

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query](https://tanstack.com/query/latest)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Zustand](https://github.com/pmndrs/zustand)
