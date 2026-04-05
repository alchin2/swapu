# diamondhacks2026

## Overview

TradeSwap is a platform for negotiating and executing hardware trades. It consists of a React unified frontend leveraging Vite and shadcn/ui and a FastAPI backend powered by Supabase PostgreSQL.

## Features
- **Guest Accounts**: Switch between users using the guest account selector on the Profile page.
- **Item Management**: View and list items for trade. 
- **AI Assisted Trades**: Agents propose and negotiate trade combinations on behalf of users.
- **Real-time Chat**: Coordinate and finalize details.

## Backend Development
The backend is written in Python (FastAPI). Key domains: `users`, `items`, `deals`, `negotiation`, `chat`, `uploads`. API Reference: [src/doc/api.md](src/doc/api.md).

Requirements are in `requirements.txt`. Start backend:
```bash
vite run uvicorn src.app:app --reload
```
or similar depending on setup.

## Frontend Development
The frontend is written in React + TypeScript + Vite.

Install dependencies and start:
```bash
pnpm install
pnpm run dev
```

## Environment Variables

The backend requires the following environment variables to run properly. Create a `.env` file in the root directory:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key

# Optional (for S3 image uploads)
AWS_S3_BUCKET=your_s3_bucket
AWS_REGION=your_s3_region
AWS_ACCESS_KEY_ID=your_access_key # Or ACCESS_KEY
AWS_SECRET_ACCESS_KEY=your_secret_key # Or SECRET_ACCESS_KEY
```

## Technologies Used

### Frontend
- **React (v18)** - UI Library
- **Vite** - Build Tool
- **Tailwind CSS (v4)** - Styling
- **Shadcn UI / Radix UI** - Accessible UI Components
- **React Router (v7)** - Routing
- **Lucide React** - Icons

### Backend 
- **Python (v3.11+)**
- **FastAPI** - Web Framework
- **Supabase (PostgreSQL)** - Database
- **OpenAI API** - AI Negotiation Agents
- **WebSockets** - Real-time Chat
- **AWS S3** - Image Storage

## Project Structure
- `src/app/` - React frontend application and components
- `src/controller/` - FastAPI REST and WebSocket routes
- `src/service/` - Backend business logic
- `src/agents/` - AI negotiation logic and OpenAi integration
- `src/database/` - Supabase client setup
- `src/doc/` - API documentation