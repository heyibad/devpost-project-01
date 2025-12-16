# Sahulat AI - Multi-Tenant AI Agents Platform

A premium glass-look SaaS platform built for Pakistan's informal economy. Sahulat AI empowers micro-entrepreneurs with AI-powered business automation agents for sales, payments, inventory, accounts, and marketing.

## 🌟 Features

- **Premium Glass Morphism Design** - Beautiful, modern UI with light greenish theme
- **AI-Powered Chat Interface** - Real-time streaming chat with markdown support
- **Multi-Agent System** - Sales, Payment, Inventory, Accounts & Marketing agents
- **Authentication** - Email/password and Google OAuth support
- **Connected Tools** - Integration management for QuickBooks, Google Sheets, WhatsApp
- **Responsive Design** - Works seamlessly across all devices

## 🚀 Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API (see API Configuration section)

### Installation

1. Clone the repository:
```bash
git clone <YOUR_GIT_URL>
cd <YOUR_PROJECT_NAME>
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
```bash
# Create a .env file based on .env.example
cp .env.example .env

# Edit .env and add your API base URL
VITE_API_BASE_URL=https://your-backend-api.com
```

4. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:8080`

## 📁 Project Structure

```
src/
├── components/         # Reusable UI components
│   ├── ui/            # shadcn/ui components
│   ├── AuthModal.tsx  # Authentication modal
│   ├── ChatSidebar.tsx # Chat sidebar navigation
│   └── ConnectedToolsPopup.tsx # Tools connection popup
├── pages/             # Application pages
│   ├── Landing.tsx    # Landing page
│   ├── Chat.tsx       # Main chat interface
│   ├── Payments.tsx   # Agent payments dashboard
│   ├── SalesConnector.tsx # WhatsApp integration
│   ├── AccountsConfig.tsx # QuickBooks configuration
│   ├── InventoryConfig.tsx # Spreadsheet integration
│   ├── Settings.tsx   # User settings
│   └── NotFound.tsx   # 404 page
├── lib/              # Utilities and API clients
│   ├── api.ts        # API client and endpoints
│   └── utils.ts      # Utility functions
└── index.css         # Global styles and design tokens
```

## 🎨 Design System

The application uses a custom design system with:
- **Colors**: Light mint/sage green primary palette (HSL-based)
- **Glass Effects**: Backdrop blur with transparency
- **Typography**: Inter font family
- **Animations**: Float, glow, and smooth transitions

All design tokens are defined in `src/index.css` and `tailwind.config.ts`.

## 🔌 API Integration

The application connects to a backend API for:
- User authentication (register, login, Google OAuth)
- Chat streaming with AI agents
- Agent configuration management

### API Endpoints Used

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/oauth/google/auth-url` - Google OAuth URL
- `POST /api/v1/oauth/google/token` - Google token exchange
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/chat/stream` - Streaming chat endpoint

See the OpenAPI schema in the project documentation for full API details.

## 🛠️ Technologies

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **React Router** - Navigation
- **React Query** - Data fetching
- **React Markdown** - Markdown rendering
- **Axios** - HTTP client

## 📦 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🎯 Key Features Implemented

### Landing Page
- Animated hero section
- AI agents showcase
- Connected services display
- Pricing plans (Starter, Business, Enterprise)
- Authentication modals

### Chat Interface
- Real-time streaming responses
- Markdown rendering
- Message persistence
- Thinking indicator during AI processing
- Connected tools management popup

### Sidebar Navigation
- Current chat view
- Agent Payments dashboard
- Sales Connector (WhatsApp)
- Accounts Agent (QuickBooks)
- Inventory Config (Spreadsheet)
- Settings

## 🔐 Authentication

The app supports two authentication methods:
1. **Email/Password** - Traditional authentication
2. **Google OAuth** - Social login

User tokens are stored in localStorage for session persistence.

## 🌐 Deployment

To deploy this application:

1. Build the project:
```bash
npm run build
```

2. Deploy the `dist` folder to your hosting provider

3. Configure environment variables on your hosting platform

## 📄 License

This project is built with Lovable. See [Lovable Documentation](https://docs.lovable.dev/) for more information.

## 🤝 Support

For issues and questions:
- Check the [Lovable Documentation](https://docs.lovable.dev/)
- Join the [Lovable Discord Community](https://discord.gg/lovable)

---

Built with ❤️ for Pakistan's entrepreneurs
