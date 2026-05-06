# Real-time Chat System

## Goal
Build a real-time chat application with WebSocket support, message persistence, and user presence indicators.

## Why
Our application needs real-time communication capabilities for customer support and team collaboration. Current email-based communication is too slow for time-sensitive issues.

## Components

### 1. Frontend (React + TypeScript)

#### Chat UI (`src/components/Chat/`)
- **ChatContainer** (`ChatContainer.tsx`)
  - Main chat layout with message list and input
  - User list sidebar showing online/offline status
  - Responsive design (desktop and mobile)

- **MessageList** (`MessageList.tsx`)
  - Scrollable message feed
  - Auto-scroll to bottom on new message
  - Infinite scroll for message history
  - Message grouping by sender and time

- **Message** (`Message.tsx`)
  - Display single message with avatar, name, timestamp
  - Support for text and basic formatting (bold, italic, code)
  - "Delivered" and "Read" indicators
  - Own messages aligned right, others aligned left

- **MessageInput** (`MessageInput.tsx`)
  - Text input with send button
  - Character counter (max 1000 chars)
  - Enter to send, Shift+Enter for newline
  - Basic text formatting toolbar
  - Typing indicator ("User is typing...")

- **UserList** (`UserList.tsx`)
  - List of users in current chat room
  - Online/offline status with green/gray dot
  - Click user to view profile or start DM

#### WebSocket Client (`src/services/websocket.ts`)
- Connect to WebSocket server with auth token
- Reconnection logic with exponential backoff
- Event handlers for: message received, user joined/left, typing indicator
- Send message, mark as read, broadcast typing status
- Connection status indicator

### 2. Backend (Node.js + Express + Socket.io)

#### WebSocket Server (`src/websocket/`)
- **server.js**: Socket.io server setup and configuration
  - JWT authentication middleware
  - Room management (join/leave)
  - Connection/disconnection handlers
  
- **messageHandler.js**: Message event handlers
  - Receive message → validate → persist → broadcast
  - Handle typing indicators
  - Mark messages as delivered/read

- **presenceHandler.js**: User presence tracking
  - Update Redis on user connect/disconnect
  - Broadcast presence changes to room members
  - Heartbeat to detect stale connections

#### REST API (`src/routes/`)
- **GET /api/chat/rooms** (`chat.js`)
  - List all chat rooms for authenticated user
  - Include unread message count per room
  
- **GET /api/chat/rooms/:roomId/messages** (`chat.js`)
  - Fetch message history with pagination
  - Query params: before (cursor), limit (default 50)
  - Returns messages with sender info
  
- **POST /api/chat/rooms/:roomId/messages** (`chat.js`)
  - Send message (fallback if WebSocket unavailable)
  - Same validation as WebSocket handler
  
- **GET /api/chat/users** (`chat.js`)
  - List users in a room
  - Include presence status (online/offline, last seen)

#### Database Models (`src/models/`)
- **Message** (`Message.js`)
  - Fields: id, roomId, userId, content, createdAt, deliveredAt, readAt
  - Indexes: roomId + createdAt (for pagination)
  
- **Room** (`Room.js`)
  - Fields: id, name, type (group/dm), createdAt, updatedAt
  - Members relationship (many-to-many with User)

- **RoomMember** (`RoomMember.js`)
  - Junction table: roomId, userId, joinedAt, lastReadAt
  - Track unread count per user per room

#### Redis for Presence (`src/services/redis.js`)
- Store online users: `SET user:{userId}:online 1 EX 300` (5 min expiry)
- Store user status: `SET user:{userId}:status "active|away|busy"`
- Get all online users in room: `SMEMBERS room:{roomId}:online`

### 3. Infrastructure

#### Docker Setup (`docker/`)
- **docker-compose.yml**
  - Services: app (Node.js), postgres, redis
  - Network configuration for service communication
  - Volume mounts for persistence

- **Dockerfile** (`Dockerfile`)
  - Multi-stage build (build → production)
  - Node 18 Alpine base image
  - Install dependencies, build TypeScript
  - Health check endpoint

#### Environment Configuration (`.env.example`)
- Database connection strings
- Redis connection URL
- JWT secret for authentication
- WebSocket server port
- CORS allowed origins

#### Deployment Scripts (`scripts/`)
- `deploy.sh`: Build and deploy to staging/production
- `migrate.sh`: Run database migrations
- `seed.sh`: Seed test data for development

### 4. Testing

#### Unit Tests
- **Backend message handler** (`src/websocket/__tests__/messageHandler.test.js`)
  - Message validation (length, content)
  - Persistence to database
  - Broadcasting to room members
  
- **Backend presence handler** (`src/websocket/__tests__/presenceHandler.test.js`)
  - Redis updates on connect/disconnect
  - Presence broadcast logic
  - Stale connection detection

- **Frontend components** (`src/components/Chat/__tests__/`)
  - MessageList renders messages correctly
  - Message component displays formatted content
  - MessageInput validates character limit
  - UserList shows online status

#### Integration Tests
- **WebSocket communication** (`tests/integration/websocket.test.js`)
  - Client connects with valid auth token
  - Client rejected with invalid token
  - Message sent and received by other clients
  - Typing indicator broadcast works
  
- **Message persistence** (`tests/integration/messages.test.js`)
  - Message saved to database after WebSocket send
  - Message history retrieved via REST API
  - Pagination works correctly

#### E2E Tests (Playwright)
- **Chat flow** (`tests/e2e/chat.spec.ts`)
  - User A sends message, User B receives it
  - User presence updates when online/offline
  - Unread count increments/decrements correctly
  - Message history loads on scroll

#### Load Testing
- **Concurrent connections** (`tests/load/connections.test.js`)
  - 100+ simultaneous WebSocket connections
  - Measure latency and throughput
  - Check for memory leaks

## Technical Constraints
- **Frontend**: React 18, TypeScript, Socket.io-client, Tailwind CSS
- **Backend**: Node.js 18, Express 4, Socket.io 4, JWT for auth
- **Database**: PostgreSQL 15 with pg driver
- **Cache**: Redis 7 for presence tracking
- **Testing**: Jest, React Testing Library, Playwright
- **Deployment**: Docker + Docker Compose
- Existing auth system at `src/middleware/auth.js` (JWT-based)

## File Ownership (to avoid conflicts)
- **Frontend Dev**: All files under `src/components/Chat/`, `src/services/websocket.ts`
- **Backend Dev**: All files under `src/websocket/`, `src/routes/chat.js`, `src/models/`, `src/services/redis.js`
- **Infrastructure Dev**: All files under `docker/`, `.env.example`, `scripts/`, `Dockerfile`
- **Testing Dev**: All files under `tests/`

## Dependencies
1. Infrastructure must set up Docker environment first (Postgres, Redis)
2. Backend must implement database models before message persistence
3. Backend must implement WebSocket server before frontend integration
4. Frontend can develop UI components in parallel with backend (use mocks)
5. Testing can write tests alongside development

## Acceptance Criteria
- ✅ Multiple users can chat in real-time via WebSocket
- ✅ Messages persist to PostgreSQL and can be retrieved on reconnection
- ✅ User presence (online/offline) is accurate and updates in <2 seconds
- ✅ System handles 100+ concurrent WebSocket connections without degradation
- ✅ Messages display with proper formatting, avatars, and timestamps
- ✅ Unread message count updates correctly
- ✅ Typing indicators show when users are typing
- ✅ Message history loads with pagination (infinite scroll)
- ✅ WebSocket reconnection works automatically with exponential backoff
- ✅ Test coverage >85% for critical paths (message send/receive, presence)
- ✅ Docker setup allows easy local development (`docker-compose up`)
- ✅ No XSS vulnerabilities (message content sanitized)
- ✅ Works on desktop and mobile browsers

## Estimated Tasks

### Backend (8 tasks)
1. Create Message, Room, RoomMember models with migrations
2. Implement Redis service for presence tracking
3. Create WebSocket server with Socket.io + JWT auth
4. Implement message handler (receive, validate, persist, broadcast)
5. Implement presence handler (connect/disconnect, Redis updates)
6. Create REST API endpoints for room list and message history
7. Write backend unit tests for handlers
8. Write integration tests for WebSocket and persistence

### Frontend (7 tasks)
9. Create ChatContainer layout and routing
10. Implement MessageList with infinite scroll
11. Create Message component with formatting
12. Implement MessageInput with validation and typing indicator
13. Create UserList with presence indicators
14. Implement WebSocket client service with reconnection
15. Write frontend component tests

### Infrastructure (4 tasks)
16. Create docker-compose.yml with all services
17. Write Dockerfile for Node.js app with multi-stage build
18. Add environment configuration template (.env.example)
19. Write deployment and migration scripts

### Testing (4 tasks)
20. Write E2E tests with Playwright for chat flow
21. Write load tests for concurrent connections
22. Verify test coverage >85%
23. Manual testing and bug fixes

**Total**: ~23 tasks → Suggest 4 teammates (Frontend, Backend, Infrastructure, Testing)

## Performance Requirements
- Message delivery latency: <200ms (same region)
- Typing indicator latency: <100ms
- Connection establishment: <1 second
- Message history load: <500ms for 50 messages
- Support 100+ concurrent users per server
- Database queries <50ms (indexed properly)

## Security Considerations
- JWT token validation on WebSocket connect
- Message content sanitization to prevent XSS
- Rate limiting: max 10 messages/second per user
- Room access control (verify user is member)
- CORS configuration for allowed origins
- No sensitive data in WebSocket errors
