#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           AIRPORT AIP LOOKUP - QUICK START                        ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Starting Airpo    rt AIP Lookup application..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    exit 1
fi

# Check if backend dependencies are installed
if [ ! -d "__pycache__" ] && [ ! -f "scrapers/airport_scraper.pyc" ]; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Start backend in background
echo "🔧 Starting Backend API (Flask)..."
python3 app.py > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Start frontend in background
echo "⚛️  Starting Frontend (Next.js)..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Application is starting up!"
echo ""
echo "📊 Services:"
echo "   Backend API:  http://localhost:8080"
echo "   Frontend UI:  http://localhost:3000"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Waiting for services to be ready..."
sleep 5

# Try to open browser
if command -v open &> /dev/null; then
    echo "🌐 Opening browser..."
    open http://localhost:3000
fi

echo "✅ Done! Application is running."
echo ""

# Keep script running
wait

