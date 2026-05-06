# Add User Profile Feature

## Goal
Add a user profile page where users can view and edit their personal information.

## Why
Users have requested the ability to manage their profile data. Currently, profile information can only be updated by admins, which is creating support tickets.

## Components

### 1. Frontend (React)
- **Profile view page** (`src/components/Profile/ProfileView.tsx`)
  - Display user's name, email, and avatar
  - "Edit Profile" button to enter edit mode
  
- **Profile edit form** (`src/components/Profile/ProfileEdit.tsx`)
  - Form with fields for name and avatar upload
  - Email field (read-only, can't be changed)
  - Save and Cancel buttons
  - Client-side validation (name required, max 100 chars)

- **Avatar upload component** (`src/components/Profile/AvatarUpload.tsx`)
  - Drag-and-drop or click to upload
  - Image preview before save
  - Max 2MB file size, JPG/PNG only
  - Crop to 200x200 square

### 2. Backend (Node.js/Express)
- **GET /api/profile** (`src/routes/profile.js`)
  - Returns authenticated user's profile data
  - Fields: id, name, email, avatarUrl, createdAt, updatedAt
  
- **PUT /api/profile** (`src/routes/profile.js`)
  - Updates authenticated user's profile
  - Accepts: name, avatar (file upload)
  - Validates: name required, 1-100 chars; avatar max 2MB
  - Uploads avatar to S3 bucket `user-avatars/`
  - Returns updated profile data

- **Profile model updates** (`src/models/User.js`)
  - Add `avatarUrl` field (string, nullable)
  - Add validation rules for name length

### 3. Tests
- **Frontend component tests** (`src/components/Profile/__tests__/`)
  - ProfileView renders user data correctly
  - ProfileEdit form validation works
  - Avatar upload component handles file selection
  - Save button triggers API call

- **Backend API tests** (`src/routes/__tests__/profile.test.js`)
  - GET /api/profile returns 200 with user data
  - GET /api/profile returns 401 if not authenticated
  - PUT /api/profile updates name successfully
  - PUT /api/profile uploads avatar to S3
  - PUT /api/profile returns 400 for invalid name
  - PUT /api/profile returns 413 for oversized avatar

- **Integration test** (`tests/integration/profile.test.js`)
  - Full flow: view profile → edit name and avatar → save → see updates

## Technical Constraints
- React 18 with TypeScript
- Express.js backend with JWT authentication middleware
- AWS S3 for avatar storage (already configured)
- Jest for testing
- Existing auth middleware at `src/middleware/auth.js`
- Existing error handler at `src/middleware/errorHandler.js`

## File Ownership (to avoid conflicts)
- **Frontend Developer**: All files under `src/components/Profile/`
- **Backend Developer**: All files under `src/routes/profile.js`, `src/models/User.js`, and backend tests

## Dependencies
- Backend must implement API endpoints before frontend can integrate (GET before PUT)
- Avatar upload component can be developed in parallel
- Tests should be written alongside implementation

## Acceptance Criteria
- ✅ Users can view their profile (name, email, avatar)
- ✅ Users can edit their name and avatar
- ✅ Changes are persisted to database
- ✅ Avatar is uploaded to S3 and URL stored
- ✅ Form validation on frontend and backend
- ✅ Test coverage >80% for new code
- ✅ No breaking changes to existing user model
- ✅ Works on desktop and mobile screens

## Estimated Tasks
1. Create Profile model updates
2. Implement GET /api/profile endpoint
3. Implement PUT /api/profile endpoint with S3 upload
4. Create ProfileView component
5. Create ProfileEdit component with validation
6. Create AvatarUpload component
7. Add routing for profile page
8. Write backend API tests
9. Write frontend component tests
10. Write integration test
11. Manual testing and bug fixes

**Total**: ~11 tasks → Suggest 2 teammates (Frontend + Backend/Testing)
