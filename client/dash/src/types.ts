export interface Instrument {
    internalCode: string;
    bloombergTicker: string;
    reutersTicker: string;
    instrumentType: string;
    currency: string;
    assetClass: string;
}

export interface Position {
    instrument: Instrument;
    quantity: number;
    dailyPnL: number;
    totalPnL: number;
    lastPrice: number;
    openingPrice: number;
    entryPrice: number;
    positionValue: number;
}

export interface RiskMetrics {
    var95: number;
    var99: number;
    maxDrawdown: number;
    exposure: number;
    riskLimit: number;
    volatility: number;
}

export interface Strategy {
    id: number;
    name: string;
    selected: boolean;
    positions: Position[];
    riskMetrics: RiskMetrics;
}

export interface WebSocketMessage {
    type: 'initial' | 'update' | 'toggle';
    data: {
        strategies?: Strategy[];
        strategyId?: number;
        prices?: Record<string, number>;
    };
} 