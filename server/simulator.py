import asyncio
from typing import Dict, List
from models import Strategy, RiskMetrics, AssetClass, AssetParams, Position
import logging
import numpy as np
import math
from datetime import datetime
from scipy.stats import multivariate_normal

logger = logging.getLogger(__name__)

class MarketSimulator:
    def __init__(self, instruments: Dict[str, Dict], initial_prices: Dict[str, float]):
        self.instruments = instruments
        self.current_prices = initial_prices.copy()
        self.opening_prices = initial_prices.copy()  # Store opening prices for client-side P&L
        self.price_history: Dict[str, List[float]] = {symbol: [price] for symbol, price in initial_prices.items()}
        self.current_returns: Dict[str, float] = {symbol: 0.0 for symbol in initial_prices.keys()}
        self.last_update = datetime.now()
        
        # Define asset parameters based on asset class
        self.asset_params = {
            "AAPL": AssetParams(
                base_volatility=0.02,
                mean_reversion=0.1,
                long_term_mean=0.0002,
                jump_probability=0.05,
                jump_scale=0.03,
                beta=1.2,
                asset_class=AssetClass.TECH
            ),
            "MSFT": AssetParams(
                base_volatility=0.018,
                mean_reversion=0.08,
                long_term_mean=0.00015,
                jump_probability=0.04,
                jump_scale=0.025,
                beta=1.1,
                asset_class=AssetClass.TECH
            ),
            "GOOGL": AssetParams(
                base_volatility=0.022,
                mean_reversion=0.12,
                long_term_mean=0.00025,
                jump_probability=0.06,
                jump_scale=0.035,
                beta=1.3,
                asset_class=AssetClass.TECH
            ),
            "TSLA": AssetParams(
                base_volatility=0.03,
                mean_reversion=0.15,
                long_term_mean=0.0003,
                jump_probability=0.08,
                jump_scale=0.04,
                beta=1.5,
                asset_class=AssetClass.TECH
            ),
            "AMZN": AssetParams(
                base_volatility=0.02,
                mean_reversion=0.1,
                long_term_mean=0.0002,
                jump_probability=0.05,
                jump_scale=0.03,
                beta=1.2,
                asset_class=AssetClass.TECH
            )
        }

        # Define correlation matrix
        self.correlation_matrix = np.array([
            [1.0, 0.7, 0.6, 0.5, 0.4],  # AAPL
            [0.7, 1.0, 0.8, 0.4, 0.5],  # MSFT
            [0.6, 0.8, 1.0, 0.3, 0.6],  # GOOGL
            [0.5, 0.4, 0.3, 1.0, 0.2],  # TSLA
            [0.4, 0.5, 0.6, 0.2, 1.0]   # AMZN
        ])

        # Market parameters
        self.market_volatility = 0.015
        self.risk_free_rate = 0.00005  # Daily risk-free rate
        
        logger.info("Market simulator initialized with base prices")

    def simulate_returns(self, dt: float = 1.0/252) -> Dict[str, float]:
        """Simulate correlated returns for all assets"""
        n_assets = len(self.asset_params)
        
        # Generate correlated normal random variables
        cov_matrix = self.correlation_matrix * np.outer(
            [params.base_volatility for params in self.asset_params.values()],
            [params.base_volatility for params in self.asset_params.values()]
        )
        
        # Generate market return
        market_return = np.random.normal(0, self.market_volatility * np.sqrt(dt))
        
        # Generate idiosyncratic returns
        idiosyncratic_returns = multivariate_normal.rvs(
            mean=np.zeros(n_assets),
            cov=cov_matrix * dt
        )
        
        # Combine market and idiosyncratic returns
        returns = {}
        for i, (symbol, params) in enumerate(self.asset_params.items()):
            # Mean reversion component
            mean_reversion = params.mean_reversion * (
                params.long_term_mean - self.current_returns.get(symbol, 0)
            ) * dt
            
            # Market component (CAPM)
            market_component = params.beta * market_return
            
            # Jump component
            jump = 0
            if np.random.random() < params.jump_probability:
                jump = np.random.normal(0, params.jump_scale)
            
            # Asset class specific components
            asset_class_return = self._get_asset_class_return(symbol, params)
            
            # Total return
            total_return = (
                self.risk_free_rate * dt +
                mean_reversion +
                market_component +
                idiosyncratic_returns[i] +
                jump +
                asset_class_return
            )
            
            returns[symbol] = total_return
        
        self.current_returns = returns
        return returns

    def _get_asset_class_return(self, symbol: str, params: AssetParams) -> float:
        """Get asset class specific return component"""
        if params.asset_class == AssetClass.TECH:
            return self._tech_stock_model(symbol, params)
        elif params.asset_class == AssetClass.COMMODITY:
            return self._commodity_model(symbol, params)
        else:
            return 0.0

    def _tech_stock_model(self, symbol: str, params: AssetParams) -> float:
        """Specialized model for technology stocks"""
        # Momentum effect
        momentum = self._calculate_momentum(symbol)
        momentum_effect = 0.1 * momentum
        
        # News impact (simulated)
        news_impact = 0
        if np.random.random() < 0.1:  # 10% chance of news
            news_impact = np.random.normal(0, 0.02)
        
        return momentum_effect + news_impact

    def _commodity_model(self, symbol: str, params: AssetParams) -> float:
        """Specialized model for commodities"""
        # Seasonality
        seasonality = self._calculate_seasonality()
        
        # Supply/demand shocks
        shock = 0
        if np.random.random() < 0.05:  # 5% chance of supply/demand shock
            shock = np.random.normal(0, 0.03)
        
        return seasonality + shock

    def _calculate_momentum(self, symbol: str, lookback: int = 20) -> float:
        """Calculate price momentum"""
        prices = self.price_history[symbol][-lookback:]
        if len(prices) < 2:
            return 0
        returns = np.diff(np.log(prices))
        return np.mean(returns)

    def _calculate_seasonality(self) -> float:
        """Calculate seasonal component"""
        return 0.0001 * np.sin(2 * np.pi * datetime.now().timetuple().tm_yday / 365)

    def initialize_position(self, instrument: Dict, quantity: float, price: float) -> Position:
        """Initialize a new position with all required fields"""
        return {
            "instrument": instrument,
            "quantity": quantity,
            "lastPrice": price,
            "openingPrice": price,  # Initialize with current price
            "entryPrice": price,    # Initialize with current price
            "totalCost": price * quantity
        }

    def update_prices(self) -> Dict[str, float]:
        """Update prices using the simulated returns"""
        returns = self.simulate_returns()
        new_prices = {}
        
        for symbol, ret in returns.items():
            new_price = self.current_prices[symbol] * np.exp(ret)
            new_prices[symbol] = new_price
            self.price_history[symbol].append(new_price)
            
            # Keep only last 1000 prices
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
            "var95": abs(var95),
            "var99": abs(var99),
            "max_drawdown": max_drawdown
        }

    def update_strategy_positions(self, strategy: Strategy) -> None:
        """Update all positions in a strategy with new prices"""
        new_prices = self.current_prices
        
        for position in strategy["positions"]:
            symbol = position["instrument"]["internalCode"]
            new_price = new_prices[symbol]
            
            # Update position with new price
            position["lastPrice"] = new_price

    def calculate_position_metrics(self, positions: List[Position]) -> Dict[str, float]:
        """Calculate portfolio-level metrics based on raw data"""
        total_exposure = 0.0
        total_var95 = 0.0
        total_var99 = 0.0
        max_drawdown = 0.0
        portfolio_volatility = 0.0
        
        # Calculate portfolio weights and exposures
        weights = {}
        exposures = {}
        for position in positions:
            symbol = position["instrument"]["internalCode"]
            exposure = abs(position["quantity"] * position["lastPrice"])
            exposures[symbol] = exposure
            total_exposure += exposure
        
        # Normalize weights
        if total_exposure > 0:
            weights = {symbol: exp/total_exposure for symbol, exp in exposures.items()}
        
        # Calculate portfolio metrics
        for position in positions:
            symbol = position["instrument"]["internalCode"]
            metrics = self.calculate_metrics(symbol)
            
            # Portfolio VaR calculation (considering correlations)
            total_var95 += metrics["var95"] * weights[symbol]
            total_var99 += metrics["var99"] * weights[symbol]
            
            if metrics["max_drawdown"] > max_drawdown:
                max_drawdown = metrics["max_drawdown"]
            
            # Portfolio volatility (considering correlations)
            portfolio_volatility += weights[symbol] * metrics["volatility"]
        
        return {
            "exposure": total_exposure,
            "var95": total_var95,
            "var99": total_var99,
            "max_drawdown": max_drawdown,
            "volatility": portfolio_volatility,
            "risk_limit": total_exposure * 1.5
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