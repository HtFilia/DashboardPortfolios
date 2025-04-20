from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Set
from models import Strategy, Position, FinancialInstrument
import asyncio
from contextlib import asynccontextmanager
import logging
import signal
import sys
import random

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global variables
active_connections: List[WebSocket] = []
selected_strategies: Set[int] = set()
broadcast_task = None
stop_broadcast = False

# Sample data (same as frontend for now)
instruments: Dict[str, FinancialInstrument] = {
    "AAPL": {
        "internalCode": "AAPL",
        "bloombergTicker": "AAPL US",
        "reutersTicker": "AAPL.O",
        "instrumentType": "Equity",
        "currency": "USD"
    },
    "MSFT": {
        "internalCode": "MSFT",
        "bloombergTicker": "MSFT US",
        "reutersTicker": "MSFT.O",
        "instrumentType": "Equity",
        "currency": "USD"
    },
    "GOOGL": {
        "internalCode": "GOOGL",
        "bloombergTicker": "GOOGL US",
        "reutersTicker": "GOOGL.O",
        "instrumentType": "Equity",
        "currency": "USD"
    },
    "TSLA": {
        "internalCode": "TSLA",
        "bloombergTicker": "TSLA US",
        "reutersTicker": "TSLA.O",
        "instrumentType": "Equity",
        "currency": "USD"
    },
    "AMZN": {
        "internalCode": "AMZN",
        "bloombergTicker": "AMZN US",
        "reutersTicker": "AMZN.O",
        "instrumentType": "Equity",
        "currency": "USD"
    }
}

def create_position(instrument: FinancialInstrument, quantity: float, dailyPnL: float, totalPnL: float) -> Position:
    return {
        "instrument": instrument,
        "quantity": quantity,
        "dailyPnL": dailyPnL,
        "totalPnL": totalPnL
    }

# Sample strategies data
strategies: List[Strategy] = [
    {
        "id": 1,
        "name": "Long-Term Growth",
        "selected": False,
        "positions": [
            create_position(instruments["AAPL"], 100, -20.156497489679737, -1738.6820035429564),
            create_position(instruments["MSFT"], 50, 406.3260936421216, 3328.5706040017653),
            create_position(instruments["GOOGL"], 25, 49.27212870692941, 851.4151565983233)
        ],
        "riskMetrics": {
            "var95": 1971.7720862429685,
            "var99": 394.3544172485937,
            "maxDrawdown": 3943.544172485937,
            "exposure": 39435.44172485937,
            "riskLimit": 59153.16258728905
        }
    },
    {
        "id": 2,
        "name": "Value Investing",
        "selected": False,
        "positions": [
            create_position(instruments["MSFT"], 75, 609.4891404631824, 4992.855906002649),
            create_position(instruments["TSLA"], 30, -236.80641785510318, -4537.268646917977),
            create_position(instruments["AMZN"], 40, 244.24864303803247, 1374.2329314315225)
        ],
        "riskMetrics": {
            "var95": 1983.3465682823055,
            "var99": 396.6693136564611,
            "maxDrawdown": 3966.693136564611,
            "exposure": 39666.93136564611,
            "riskLimit": 59500.39704846917
        }
    },
    {
        "id": 3,
        "name": "Dividend Focus",
        "selected": False,
        "positions": [
            create_position(instruments["AAPL"], 50, -10.078248744839868, -243.8410017714782),
            create_position(instruments["MSFT"], 100, 812.6521872842432, 8157.8912080035325),
            create_position(instruments["AMZN"], 20, 122.12432151901623, 1437.616465715761)
        ],
        "riskMetrics": {
            "var95": 2416.234913002921,
            "var99": 483.24698260058426,
            "maxDrawdown": 4832.469826005842,
            "exposure": 48324.69826005842,
            "riskLimit": 72487.04739008764
        }
    },
    {
        "id": 4,
        "name": "Sector Rotation",
        "selected": False,
        "positions": [
            create_position(instruments["TSLA"], 50, -394.67736309183863, -8812.364411529961),
            create_position(instruments["GOOGL"], 40, 78.83540593108705, 2963.0142505573176),
            create_position(instruments["AMZN"], 30, 183.18648227852435, 2156.1746985736418)
        ],
        "riskMetrics": {
            "var95": 1028.3672262558887,
            "var99": 205.67344525117772,
            "maxDrawdown": 2056.7344525117774,
            "exposure": 20567.344525117773,
            "riskLimit": 30851.016787676657
        }
    },
    {
        "id": 5,
        "name": "Market Neutral",
        "selected": False,
        "positions": [
            create_position(instruments["AAPL"], 100, -20.156497489679737, -487.9320035429564),
            create_position(instruments["TSLA"], -100, 789.3547261836773, 16374.978823059924),
            create_position(instruments["GOOGL"], 50, 98.54425741385882, 2703.080313196647),
            create_position(instruments["AMZN"], -50, -305.3108037975406, -2718.0411642894032)
        ],
        "riskMetrics": {
            "var95": 2654.7171918769022,
            "var99": 530.9434383753804,
            "maxDrawdown": 5309.4343837538045,
            "exposure": 53094.34383753804,
            "riskLimit": 79641.51575630707
        }
    }
]

async def broadcast_updates():
    global stop_broadcast
    while not stop_broadcast:
        try:
            # Update P&L values
            for strategy in strategies:
                for position in strategy["positions"]:
                    position["dailyPnL"] = random.uniform(-500, 500)
                    position["totalPnL"] = random.uniform(-10000, 10000)

            # Prepare update message
            message = {
                "type": "update",
                "data": {
                    "strategies": strategies
                }
            }

            # Send to all active connections
            for connection in active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to connection: {e}")
                    active_connections.remove(connection)

            await asyncio.sleep(1)  # Update every second
        except Exception as e:
            logger.error(f"Error in broadcast loop: {e}")
            if stop_broadcast:
                break
            await asyncio.sleep(1)  # Wait before retrying

async def cleanup():
    global stop_broadcast, broadcast_task
    logger.info("Cleaning up resources...")
    stop_broadcast = True
    
    # Wait for broadcast task to complete
    if broadcast_task:
        try:
            await broadcast_task
        except Exception as e:
            logger.error(f"Error waiting for broadcast task: {e}")
    
    # Close all active connections
    for connection in active_connections:
        try:
            await connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
    
    active_connections.clear()
    selected_strategies.clear()
    logger.info("Cleanup completed")

def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    asyncio.create_task(cleanup())
    sys.exit(0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global broadcast_task
    # Start broadcast task
    broadcast_task = asyncio.create_task(broadcast_updates())
    
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGBREAK, handle_shutdown)
    
    yield
    
    # Cleanup on shutdown
    await cleanup()

app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"New WebSocket connection established. Total connections: {len(active_connections)}")
    
    try:
        # Send initial state
        initial_message = {
            "type": "initial",
            "data": {
                "strategies": strategies
            }
        }
        logger.info("Sending initial state to client")
        await websocket.send_json(initial_message)
        
        # Handle messages from client
        while True:
            try:
                data = await websocket.receive_json()
                if data["type"] == "toggle":
                    strategy_id = data["data"]["strategyId"]
                    if strategy_id in selected_strategies:
                        selected_strategies.remove(strategy_id)
                    else:
                        selected_strategies.add(strategy_id)
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                break
    except WebSocketDisconnect:
        logger.info("Client disconnected")
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        active_connections.remove(websocket)
    finally:
        try:
            await websocket.close()
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001) 