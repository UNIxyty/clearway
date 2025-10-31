# Airport AIP Lookup - Modern Frontend

A professional, modern web application built with **Next.js 16**, **TypeScript**, and **shadcn/ui** for looking up real-time airport aeronautical information.

## 🚀 Tech Stack

- **Next.js 16** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Professional UI components
- **Lucide React** - Beautiful icons
- **React 19** - Latest React features

## ✨ Features

- 🎨 **Modern Design** - Professional UI with shadcn/ui components
- 🌍 **Multi-Country Support** - USA, France, Estonia, Finland, Lithuania, Latvia
- 📱 **Responsive** - Works on all devices
- ⚡ **Fast** - Optimized with Next.js
- 🎯 **Type-Safe** - Full TypeScript support
- 🌙 **Dark Mode Ready** - Built-in dark mode support

## 📦 Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8080`

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

### Build for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

## 🏗️ Project Structure

```
frontend/
├── app/
│   ├── layout.tsx      # Root layout with metadata
│   ├── page.tsx        # Main Airport Lookup page
│   └── globals.css     # Global styles
├── components/
│   └── ui/             # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── badge.tsx
│       └── separator.tsx
├── lib/
│   └── utils.ts        # Utility functions
├── package.json
└── README.md
```

## 🎨 Components Used

- **Button** - Search actions
- **Card** - Content containers
- **Input** - Airport code entry
- **Label** - Form labels
- **Badge** - Country/region indicators
- **Separator** - Visual dividers

## 🔌 API Integration

The frontend connects to the Flask backend API:

- **Endpoint**: `http://localhost:8080/api/airport`
- **Method**: POST
- **Body**: `{ "airportCode": "EVRA" }`

## 🌍 Supported Airport Codes

| Prefix | Country | Example |
|--------|---------|---------|
| K* | USA 🇺🇸 | KJFK, KLAX, KORD |
| LF* | France 🇫🇷 | LFPG, LFBO |
| EE* | Estonia 🇪🇪 | EETN |
| EF* | Finland 🇫🇮 | EFHK, EFJV |
| EY* | Lithuania 🇱🇹 | EYVI, EYSA, EYKA, EYPA |
| EV* | Latvia 🇱🇻 | EVRA, EVLA, EVLI, EVCA, EVGA, EVPA, EVRS, EVVA |

## 📝 Development

```bash
# Run development server with hot reload
npm run dev

# Lint code
npm run lint

# Type check
npx tsc --noEmit

# Build
npm run build
```

## 🎯 Future Enhancements

- [ ] Dark mode toggle
- [ ] Search history
- [ ] Favorites/bookmarks
- [ ] Export to PDF
- [ ] Map integration
- [ ] Weather integration
- [ ] Flight information

## 📄 License

This project is part of the Airport AIP Lookup system.
