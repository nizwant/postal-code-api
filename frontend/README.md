# Polish Postal Code Lookup - Frontend

A modern Next.js web application for searching Polish postal codes with multi-API support and performance comparison.

## Features

- **Dual Search Interface**: Find postal codes by address OR find addresses by postal code
- **Smart Autocomplete**: Real-time suggestions using your API's location hierarchy endpoints
- **Multi-API Support**: Switch between Flask, FastAPI, Go, and Elixir backends
- **Performance Metrics**: Real-time response time tracking and API status monitoring
- **Internationalization**: Polish and English language support
- **Dark/Light Theme**: Automatic system detection with manual override
- **Responsive Design**: Mobile-first design with Tailwind CSS

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- At least one of your postal code APIs running (Flask on :5001, FastAPI on :5002, Go on :5003, or Elixir on :5004)

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## API Integration

The frontend uses a proxy system to handle CORS and communicate with your backend APIs:

- **Flask**: http://localhost:5001
- **FastAPI**: http://localhost:5002
- **Go**: http://localhost:5003
- **Elixir**: http://localhost:5004

The app automatically detects which APIs are online and displays their status in the header.

## Architecture

- **Next.js 15** with TypeScript and Tailwind CSS
- **App Router** for modern React patterns
- **Context API** for global state management (API switching, theme, language)
- **Custom hooks** for translations and API calls
- **Proxy API routes** for CORS handling

## Key Components

- `AddressForm`: Address-to-postal-code lookup with smart autocomplete
- `PostalCodeForm`: Postal-code-to-addresses reverse lookup
- `ResultsDisplay`: Unified results table with performance metrics
- `Header`: API selector, language toggle, theme toggle
- `AppContext`: Global state management

## Usage

### Address Lookup
1. Enter city (recommended for best results)
2. Optionally add street and house number for more precision
3. Use "Advanced Options" to filter by province/county/municipality
4. Click Search to get postal code(s)

### Postal Code Lookup
1. Enter postal code in XX-XXX format
2. Click Search to get all addresses under that code

### API Switching
- Use the dropdown in the header to switch between backend APIs
- Response times are displayed next to each API
- Status indicators show API health (green=online, red=offline, yellow=checking)

## Development Notes

- The app uses a proxy at `/api/proxy/[...path]` to handle CORS with your backend APIs
- Translations are stored in `/src/locales/` as JSON files
- Theme and language preferences are persisted in localStorage
- The app is fully responsive and works on mobile devices

## Customization

To add support for additional languages:
1. Add translation file to `/src/locales/`
2. Update the language selector in `Header.tsx`
3. Add the language to the `AppContext`

To add more API endpoints:
1. Update `API_ENDPOINTS` in `/src/lib/api.ts`
2. The UI will automatically include the new endpoints
