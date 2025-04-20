import asyncio
import random
from typing import Dict, List
from models import FinancialInstrument, Position, Strategy, RiskMetrics
import logging

logger = logging.getLogger(__name__)

class PriceSimulator:
    def __init__(self, instruments: Dict[str, FinancialInstrument]):
        self.instruments = instruments
        self.base_prices = {
            "AAPL": 180.0,
            "MSFT": 350.0,
            "GOOGL": 140.0,
            "TSLA": 200.0,
            "AMZN": 170.0
        }
        self.current_prices = self.base_prices.copy()
        logger.info("Price simulator initialized with base prices")
        
    def update_prices(self):
        """Update prices with random walk"""
        for ticker in self.current_prices:
            # Random walk with 1% max change
            change = random.uniform(-0.01, 0.01)
            self.current_prices[ticker] = self.current_prices[ticker] * (1 + change)
        logger.debug(f"Updated prices: {self.current_prices}")
        return self.current_prices

    def calculate_position_pnl(self, position: Position) -> tuple[float, float]:
        """Calculate daily and total PnL for a position"""
        instrument = position["instrument"]
        ticker = instrument["internalCode"]
        current_price = self.current_prices[ticker]
        base_price = self.base_prices[ticker]
        
        daily_pnl = position["quantity"] * (current_price - base_price)
        total_pnl = position["totalPnL"] + daily_pnl
        
        return daily_pnl, total_pnl

    def calculate_strategy_metrics(self, strategy: Strategy) -> RiskMetrics:
        """Calculate risk metrics for a strategy"""
        positions = strategy["positions"]
        total_exposure = sum(abs(pos["quantity"] * self.current_prices[pos["instrument"]["internalCode"]]) 
                           for pos in positions)
        
        # Simplified risk metrics calculation
        var95 = total_exposure * 0.05  # 5% of exposure
        var99 = total_exposure * 0.01  # 1% of exposure
        max_drawdown = total_exposure * 0.1  # 10% of exposure
        
        metrics = {
            "var95": var95,
            "var99": var99,
            "maxDrawdown": max_drawdown,
            "exposure": total_exposure,
            "riskLimit": total_exposure * 1.5  # 150% of current exposure
        }
        logger.debug(f"Calculated metrics for strategy {strategy['name']}: {metrics}")
        return metrics

    async def run_simulation(self, strategies: List[Strategy], broadcast_callback):
        """Run the simulation loop"""
        logger.info("Starting simulation loop")
        while True:
            try:
                # Update prices
                self.update_prices()
                
                # Update each strategy
                for strategy in strategies:
                    # Update positions PnL
                    for position in strategy["positions"]:
                        daily_pnl, total_pnl = self.calculate_position_pnl(position)
                        position["dailyPnL"] = daily_pnl
                        position["totalPnL"] = total_pnl
                    
                    # Update risk metrics
                    strategy["riskMetrics"] = self.calculate_strategy_metrics(strategy)
                
                # Broadcast updates
                update_message = {
                    "type": "update",
                    "data": {
                        "prices": self.current_prices,
                        "strategies": strategies
                    }
                }
                logger.debug("Sending update message")
                await broadcast_callback(update_message)
                
                # Wait for next update
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(2)  # Wait before retrying 