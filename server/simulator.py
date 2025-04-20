import asyncio
from typing import Dict, List
from models import Strategy, RiskMetrics
import logging
import numpy as np
import math
from datetime import datetime

logger = logging.getLogger(__name__)

class PriceSimulator:
    def __init__(self, instruments: Dict[str, Dict], initial_prices: Dict[str, float]):
        self.instruments = instruments
        self.current_prices = initial_prices.copy()
        self.price_history: Dict[str, List[float]] = {symbol: [price] for symbol, price in initial_prices.items()}
        self.last_update = datetime.now()
        
        # Model parameters (hardcoded for now)
        self.params = {
            "AAPL": {"mu": 0.0002, "sigma": 0.02, "beta": 1.2},  # Higher beta for tech
            "MSFT": {"mu": 0.00015, "sigma": 0.018, "beta": 1.1},
            "GOOGL": {"mu": 0.00025, "sigma": 0.022, "beta": 1.3},
            "TSLA": {"mu": 0.0003, "sigma": 0.03, "beta": 1.5},  # Higher volatility for Tesla
            "AMZN": {"mu": 0.0002, "sigma": 0.02, "beta": 1.2}
        }
        
        # Market parameters
        self.market_mu = 0.0001
        self.market_sigma = 0.015
        self.risk_free_rate = 0.00005  # Daily risk-free rate
        
        logger.info("Price simulator initialized with base prices")
        
    def update_prices(self) -> Dict[str, float]:
        """Update prices using geometric Brownian motion with market correlation"""
        dt = (datetime.now() - self.last_update).total_seconds() / (24 * 3600)  # Convert to days
        self.last_update = datetime.now()
        
        # Generate market return
        market_return = np.random.normal(self.market_mu * dt, self.market_sigma * math.sqrt(dt))
        
        new_prices = {}
        for symbol, params in self.params.items():
            # Generate idiosyncratic return
            epsilon = np.random.normal(0, params["sigma"] * math.sqrt(dt))
            
            # Calculate total return (CAPM model)
            total_return = (self.risk_free_rate * dt + 
                          params["beta"] * market_return + 
                          epsilon)
            
            # Update price
            new_price = self.current_prices[symbol] * math.exp(total_return)
            new_prices[symbol] = new_price
            self.price_history[symbol].append(new_price)
            
            # Keep only last 1000 prices for calculations
            if len(self.price_history[symbol]) > 1000:
                self.price_history[symbol] = self.price_history[symbol][-1000:]
        
        self.current_prices = new_prices
        return new_prices

    def calculate_returns(self, symbol: str) -> List[float]:
        """Calculate daily returns for a symbol"""
        prices = self.price_history[symbol]
        returns = []
        for i in range(1, len(prices)):
            returns.append(math.log(prices[i] / prices[i-1]))
        return returns

    def calculate_metrics(self, symbol: str) -> Dict[str, float]:
        """Calculate risk metrics for a symbol"""
        returns = self.calculate_returns(symbol)
        if not returns:
            return {
                "volatility": 0.0,
                "var95": 0.0,
                "var99": 0.0,
                "max_drawdown": 0.0
            }
        
        # Calculate volatility (annualized)
        volatility = np.std(returns) * math.sqrt(252)
        
        # Calculate VaR (Value at Risk)
        var95 = np.percentile(returns, 5) * self.current_prices[symbol]
        var99 = np.percentile(returns, 1) * self.current_prices[symbol]
        
        # Calculate maximum drawdown
        prices = self.price_history[symbol]
        peak = prices[0]
        max_drawdown = 0.0
        for price in prices:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            "volatility": volatility,
            "var95": abs(var95),  # Convert to positive value
            "var99": abs(var99),  # Convert to positive value
            "max_drawdown": max_drawdown
        }

    def calculate_position_metrics(self, positions: List[Dict]) -> Dict[str, float]:
        """Calculate portfolio-level metrics"""
        total_exposure = 0.0
        total_var95 = 0.0
        total_var99 = 0.0
        max_drawdown = 0.0
        
        for position in positions:
            symbol = position["instrument"]["internalCode"]
            quantity = position["quantity"]
            price = self.current_prices[symbol]
            exposure = abs(quantity * price)
            total_exposure += exposure
            
            metrics = self.calculate_metrics(symbol)
            # Portfolio VaR calculation (simplified)
            total_var95 += metrics["var95"] * exposure
            total_var99 += metrics["var99"] * exposure
            
            if metrics["max_drawdown"] > max_drawdown:
                max_drawdown = metrics["max_drawdown"]
        
        # Normalize VaR by total exposure
        if total_exposure > 0:
            total_var95 /= total_exposure
            total_var99 /= total_exposure
        
        return {
            "exposure": total_exposure,
            "var95": total_var95,
            "var99": total_var99,
            "max_drawdown": max_drawdown,
            "risk_limit": total_exposure * 1.5  # 150% of exposure as risk limit
        }

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