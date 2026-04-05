# SwapU

## Overview
<img width="1299" height="705" alt="logo" src="https://github.com/user-attachments/assets/51856599-1bb2-4c8d-a60c-9603e82bd632" />
<img width="2409" height="1508" alt="homescreen" src="https://github.com/user-attachments/assets/5648f36e-0342-4fb7-b931-b2b45e192207" />
<img width="2408" height="1515" alt="ainegotiation" src="https://github.com/user-attachments/assets/c239667f-38ce-4d52-b8b8-7bbd6fa1b05f" />

The spark for SwapU came from the "campus graveyard" of unused student gear. We realized that university life is full of inefficiencies; students are constantly sitting on assets like iClickers, lab equipment, or textbooks that they no longer need, while others are continually searching through forums and marketplace discords to find those exact items.

Traditional marketplaces are too slow for the fast-paced student schedule. We wanted to take the thrill and fairness of trading and apply it to campus essentials, removing the awkwardness of manual haggling and replacing it with an intelligent, autonomous system.

Under the hood, SwapU is a platform for negotiating and executing these trades. It consists of a React unified frontend leveraging Vite and shadcn/ui, and a FastAPI backend powered by Supabase PostgreSQL.

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

```text
diamondhacks2026/
├── src/
│   ├── agents/          # AI negotiation logic and BrowserUse integration for determining prices
│   ├── app/             # React frontend root
│   │   ├── components/  # React UI components and pages
│   │   ├── contexts/    # React context providers
│   │   └── ...          # React routing and root files
│   ├── controller/      # FastAPI REST and WebSocket controllers/routes
│   ├── core/            # Application exceptions and core logic
│   ├── database/        # Supabase client setup and configuration
│   ├── doc/             # API documentation
│   ├── scripts/         # DB seeders and utility scripts
│   ├── service/         # Backend business logic and DB interactions
│   ├── styles/          # Tailwind and global CSS
│   ├── test/            # Backend automated test suite
│   ├── websocket/       # WebSocket logic implementations
│   ├── app.py           # FastAPI entry point
│   └── main.tsx         # React entry point
├── package.json         # Frontend dependencies
├── requirements.txt     # Python backend dependencies
└── vite.config.ts       # Vite and frontend proxy configuration
```
