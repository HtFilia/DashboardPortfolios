import asyncio
import signal
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Set
from contextlib import asynccontextmanager
import logging
from simulator import PriceSimulator

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
price_simulator = None

# Initial prices
initial_prices = {
    "AAPL": 180.0,
    "MSFT": 350.0,
    "GOOGL": 140.0,
    "TSLA": 200.0,
    "AMZN": 170.0
}

# Sample data (same as frontend for now)
strategies = [
    {
        "id": 1,
        "name": "Long-Term Growth",
        "selected": False,
        "positions": [
            {
                "instrument": {
                    "internalCode": "AAPL",
                    "bloombergTicker": "AAPL US",
                    "reutersTicker": "AAPL.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 100,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            },
            {
                "instrument": {
                    "internalCode": "MSFT",
                    "bloombergTicker": "MSFT US",
                    "reutersTicker": "MSFT.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 50,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            },
            {
                "instrument": {
                    "internalCode": "GOOGL",
                    "bloombergTicker": "GOOGL US",
                    "reutersTicker": "GOOGL.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 25,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            }
        ],
        "riskMetrics": {
            "var95": 0.0,
            "var99": 0.0,
            "maxDrawdown": 0.0,
            "exposure": 0.0,
            "riskLimit": 0.0
        }
    },
    {
        "id": 2,
        "name": "Value Investing",
        "selected": False,
        "positions": [
            {
                "instrument": {
                    "internalCode": "MSFT",
                    "bloombergTicker": "MSFT US",
                    "reutersTicker": "MSFT.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 75,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            },
            {
                "instrument": {
                    "internalCode": "TSLA",
                    "bloombergTicker": "TSLA US",
                    "reutersTicker": "TSLA.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 30,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            },
            {
                "instrument": {
                    "internalCode": "AMZN",
                    "bloombergTicker": "AMZN US",
                    "reutersTicker": "AMZN.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 40,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            }
        ],
        "riskMetrics": {
            "var95": 0.0,
            "var99": 0.0,
            "maxDrawdown": 0.0,
            "exposure": 0.0,
            "riskLimit": 0.0
        }
    },
    {
        "id": 3,
        "name": "Dividend Focus",
        "selected": False,
        "positions": [
            {
                "instrument": {
                    "internalCode": "AAPL",
                    "bloombergTicker": "AAPL US",
                    "reutersTicker": "AAPL.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 50,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            },
            {
                "instrument": {
                    "internalCode": "MSFT",
                    "bloombergTicker": "MSFT US",
                    "reutersTicker": "MSFT.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 100,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            },
            {
                "instrument": {
                    "internalCode": "AMZN",
                    "bloombergTicker": "AMZN US",
                    "reutersTicker": "AMZN.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 20,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            }
        ],
        "riskMetrics": {
            "var95": 0.0,
            "var99": 0.0,
            "maxDrawdown": 0.0,
            "exposure": 0.0,
            "riskLimit": 0.0
        }
    },
    {
        "id": 4,
        "name": "Sector Rotation",
        "selected": False,
        "positions": [
            {
                "instrument": {
                    "internalCode": "TSLA",
                    "bloombergTicker": "TSLA US",
                    "reutersTicker": "TSLA.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 50,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            },
            {
                "instrument": {
                    "internalCode": "GOOGL",
                    "bloombergTicker": "GOOGL US",
                    "reutersTicker": "GOOGL.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 40,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            },
            {
                "instrument": {
                    "internalCode": "AMZN",
                    "bloombergTicker": "AMZN US",
                    "reutersTicker": "AMZN.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 30,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            }
        ],
        "riskMetrics": {
            "var95": 0.0,
            "var99": 0.0,
            "maxDrawdown": 0.0,
            "exposure": 0.0,
            "riskLimit": 0.0
        }
    },
    {
        "id": 5,
        "name": "Market Neutral",
        "selected": False,
        "positions": [
            {
                "instrument": {
                    "internalCode": "AAPL",
                    "bloombergTicker": "AAPL US",
                    "reutersTicker": "AAPL.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 100,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            },
            {
                "instrument": {
                    "internalCode": "TSLA",
                    "bloombergTicker": "TSLA US",
                    "reutersTicker": "TSLA.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": -100,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            },
            {
                "instrument": {
                    "internalCode": "GOOGL",
                    "bloombergTicker": "GOOGL US",
                    "reutersTicker": "GOOGL.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": 50,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            },
            {
                "instrument": {
                    "internalCode": "AMZN",
                    "bloombergTicker": "AMZN US",
                    "reutersTicker": "AMZN.O",
                    "instrumentType": "Equity",
                    "currency": "USD"
                },
                "quantity": -50,
                "dailyPnL": 0.0,
                "totalPnL": 0.0
            }
        ],
        "riskMetrics": {
            "var95": 0.0,
            "var99": 0.0,
            "maxDrawdown": 0.0,
            "exposure": 0.0,
            "riskLimit": 0.0
        }
    }
]

async def broadcast_updates():
    global stop_broadcast
    while not stop_broadcast:
        try:
            # Update prices
            new_prices = price_simulator.update_prices()
            
            # Update positions and metrics
            for strategy in strategies:
                # Update position P&L
                for position in strategy["positions"]:
                    symbol = position["instrument"]["internalCode"]
                    old_price = position.get("last_price", initial_prices[symbol])
                    new_price = new_prices[symbol]
                    
                    # Calculate P&L
                    price_change = new_price - old_price
                    position["dailyPnL"] = position["quantity"] * price_change
                    position["totalPnL"] += position["dailyPnL"]
                    position["last_price"] = new_price
                
                # Update strategy metrics
                metrics = price_simulator.calculate_position_metrics(strategy["positions"])
                strategy["riskMetrics"] = {
                    "var95": metrics["var95"],
                    "var99": metrics["var99"],
                    "maxDrawdown": metrics["max_drawdown"],
                    "exposure": metrics["exposure"],
                    "riskLimit": metrics["risk_limit"]
                }

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
    global broadcast_task, price_simulator
    # Initialize price simulator
    price_simulator = PriceSimulator({}, initial_prices)
    
    # Start broadcast task
    broadcast_task = asyncio.create_task(broadcast_updates())
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGBREAK, handle_shutdown)
    
    yield
    
    # Cleanup on shutdown
    await cleanup()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        # Send initial data
        initial_message = {
            "type": "initial",
            "data": {
                "strategies": strategies
            }
        }
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
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)
        try:
            await websocket.close()
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001) 