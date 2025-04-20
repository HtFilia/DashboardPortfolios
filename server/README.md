# Portfolio Dashboard Backend

This is the backend server for the Portfolio Dashboard application, built with FastAPI and WebSocket support.

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

To start the server, run:
```bash
python main.py
```

The server will start on `http://localhost:8000`.

## WebSocket Endpoint

The WebSocket endpoint is available at:
```
ws://localhost:8000/ws
```

### WebSocket Message Types

1. Initial Connection:
   - The server sends the initial state with all strategies and their positions
   - Message format:
   ```json
   {
     "type": "initial",
     "data": {
       "strategies": [...]
     }
   }
   ```

2. Toggle Strategy:
   - Client can toggle a strategy's selected state
   - Message format:
   ```json
   {
     "type": "toggle_strategy",
     "strategy_id": 1
   }
   ```

3. Updates:
   - Server broadcasts updates to all connected clients
   - Message format:
   ```json
   {
     "type": "update",
     "data": {
       "strategies": [...]
     }
   }
   ```

## Data Structure

The server maintains the following data structures in memory:
- Financial Instruments
- Positions
- Strategies with Risk Metrics

All data is currently hardcoded for demonstration purposes. 