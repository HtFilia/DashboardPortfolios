import asyncio
import signal
import sys
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Set
from contextlib import asynccontextmanager
import logging
from simulator import MarketSimulator
from models import AssetClass
import json

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
market_simulator = None

# Initial prices
initial_prices = {
    "AAPL": 180.0,
    "MSFT": 350.0,
    "GOOGL": 140.0,
    "TSLA": 200.0,
    "AMZN": 170.0
}

# Sample data with asset classes
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
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 100,
                "lastPrice": initial_prices["AAPL"],
                "openingPrice": initial_prices["AAPL"],
                "entryPrice": initial_prices["AAPL"]
            },
            {
                "instrument": {
                    "internalCode": "MSFT",
                    "bloombergTicker": "MSFT US",
                    "reutersTicker": "MSFT.O",
                    "instrumentType": "Equity",
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 50,
                "lastPrice": initial_prices["MSFT"],
                "openingPrice": initial_prices["MSFT"],
                "entryPrice": initial_prices["MSFT"]
            },
            {
                "instrument": {
                    "internalCode": "GOOGL",
                    "bloombergTicker": "GOOGL US",
                    "reutersTicker": "GOOGL.O",
                    "instrumentType": "Equity",
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 25,
                "lastPrice": initial_prices["GOOGL"],
                "openingPrice": initial_prices["GOOGL"],
                "entryPrice": initial_prices["GOOGL"]
            }
        ],
        "riskMetrics": {
            "var95": 0.0,
            "var99": 0.0,
            "maxDrawdown": 0.0,
            "exposure": 0.0,
            "riskLimit": 0.0,
            "volatility": 0.0
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
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 75,
                "lastPrice": initial_prices["MSFT"],
                "openingPrice": initial_prices["MSFT"],
                "entryPrice": initial_prices["MSFT"]
            },
            {
                "instrument": {
                    "internalCode": "TSLA",
                    "bloombergTicker": "TSLA US",
                    "reutersTicker": "TSLA.O",
                    "instrumentType": "Equity",
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 30,
                "lastPrice": initial_prices["TSLA"],
                "openingPrice": initial_prices["TSLA"],
                "entryPrice": initial_prices["TSLA"]
            },
            {
                "instrument": {
                    "internalCode": "AMZN",
                    "bloombergTicker": "AMZN US",
                    "reutersTicker": "AMZN.O",
                    "instrumentType": "Equity",
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 40,
                "lastPrice": initial_prices["AMZN"],
                "openingPrice": initial_prices["AMZN"],
                "entryPrice": initial_prices["AMZN"]
            }
        ],
        "riskMetrics": {
            "var95": 0.0,
            "var99": 0.0,
            "maxDrawdown": 0.0,
            "exposure": 0.0,
            "riskLimit": 0.0,
            "volatility": 0.0
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
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 50,
                "dailyPnL": 0.0,
                "totalPnL": 0.0,
                "lastPrice": initial_prices["AAPL"]
            },
            {
                "instrument": {
                    "internalCode": "MSFT",
                    "bloombergTicker": "MSFT US",
                    "reutersTicker": "MSFT.O",
                    "instrumentType": "Equity",
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 100,
                "dailyPnL": 0.0,
                "totalPnL": 0.0,
                "lastPrice": initial_prices["MSFT"]
            },
            {
                "instrument": {
                    "internalCode": "AMZN",
                    "bloombergTicker": "AMZN US",
                    "reutersTicker": "AMZN.O",
                    "instrumentType": "Equity",
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 20,
                "dailyPnL": 0.0,
                "totalPnL": 0.0,
                "lastPrice": initial_prices["AMZN"]
            }
        ],
        "riskMetrics": {
            "var95": 0.0,
            "var99": 0.0,
            "maxDrawdown": 0.0,
            "exposure": 0.0,
            "riskLimit": 0.0,
            "volatility": 0.0
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
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 50,
                "dailyPnL": 0.0,
                "totalPnL": 0.0,
                "lastPrice": initial_prices["TSLA"]
            },
            {
                "instrument": {
                    "internalCode": "GOOGL",
                    "bloombergTicker": "GOOGL US",
                    "reutersTicker": "GOOGL.O",
                    "instrumentType": "Equity",
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 40,
                "dailyPnL": 0.0,
                "totalPnL": 0.0,
                "lastPrice": initial_prices["GOOGL"]
            },
            {
                "instrument": {
                    "internalCode": "AMZN",
                    "bloombergTicker": "AMZN US",
                    "reutersTicker": "AMZN.O",
                    "instrumentType": "Equity",
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 30,
                "dailyPnL": 0.0,
                "totalPnL": 0.0,
                "lastPrice": initial_prices["AMZN"]
            }
        ],
        "riskMetrics": {
            "var95": 0.0,
            "var99": 0.0,
            "maxDrawdown": 0.0,
            "exposure": 0.0,
            "riskLimit": 0.0,
            "volatility": 0.0
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
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 100,
                "dailyPnL": 0.0,
                "totalPnL": 0.0,
                "lastPrice": initial_prices["AAPL"]
            },
            {
                "instrument": {
                    "internalCode": "TSLA",
                    "bloombergTicker": "TSLA US",
                    "reutersTicker": "TSLA.O",
                    "instrumentType": "Equity",
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": -100,
                "dailyPnL": 0.0,
                "totalPnL": 0.0,
                "lastPrice": initial_prices["TSLA"]
            },
            {
                "instrument": {
                    "internalCode": "GOOGL",
                    "bloombergTicker": "GOOGL US",
                    "reutersTicker": "GOOGL.O",
                    "instrumentType": "Equity",
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": 50,
                "dailyPnL": 0.0,
                "totalPnL": 0.0,
                "lastPrice": initial_prices["GOOGL"]
            },
            {
                "instrument": {
                    "internalCode": "AMZN",
                    "bloombergTicker": "AMZN US",
                    "reutersTicker": "AMZN.O",
                    "instrumentType": "Equity",
                    "currency": "USD",
                    "assetClass": AssetClass.TECH.value
                },
                "quantity": -50,
                "dailyPnL": 0.0,
                "totalPnL": 0.0,
                "lastPrice": initial_prices["AMZN"]
            }
        ],
        "riskMetrics": {
            "var95": 0.0,
            "var99": 0.0,
            "maxDrawdown": 0.0,
            "exposure": 0.0,
            "riskLimit": 0.0,
            "volatility": 0.0
        }
    }
]

async def broadcast_updates():
    global stop_broadcast
    while not stop_broadcast:
        try:
            # Update prices
            new_prices = market_simulator.update_prices()
            
            # Update positions and metrics
            for strategy in strategies:
                # Update position P&L
                for position in strategy["positions"]:
                    symbol = position["instrument"]["internalCode"]
                    position["lastPrice"] = new_prices[symbol]
                
                # Update strategy metrics
                metrics = market_simulator.calculate_position_metrics(strategy["positions"])
                strategy["riskMetrics"] = {
                    "var95": metrics["var95"],
                    "var99": metrics["var99"],
                    "maxDrawdown": metrics["max_drawdown"],
                    "exposure": metrics["exposure"],
                    "volatility": metrics["volatility"],
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
    global broadcast_task, market_simulator
    # Initialize market simulator
    market_simulator = MarketSimulator({}, initial_prices)
    
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
                "prices": market_simulator.current_prices,
                "strategies": strategies
            }
        }
        logger.debug(f"Sending initial data: {json.dumps(initial_message, indent=2)}")
        await websocket.send_json(initial_message)
        
        # Handle messages from client
        while True:
            try:
                data = await websocket.receive_json()
                logger.debug(f"Received message from client: {json.dumps(data, indent=2)}")
                
                if data["type"] == "toggle_strategy":
                    strategy_id = data["strategyId"]
                    for strategy in strategies:
                        if strategy["id"] == strategy_id:
                            strategy["selected"] = not strategy["selected"]
                            logger.info(f"Toggled strategy {strategy['name']} to {strategy['selected']}")
                            break
                
            except Exception as e:
                logger.error(f"Error handling client message: {e}", exc_info=True)
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Remaining connections: {len(active_connections)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001) 