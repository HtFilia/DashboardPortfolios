import { ref } from 'vue';
import type { Strategy, WebSocketMessage } from '../types';

class WebSocketService {
    private ws: WebSocket | null = null;
    private updateCallbacks: ((data: WebSocketMessage) => void)[] = [];
    public strategies = ref<Strategy[]>([]);

    connect() {
        if (this.ws) {
            return; // Already connected
        }

        this.ws = new WebSocket('ws://localhost:9001/ws');

        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data) as WebSocketMessage;
            this.strategies.value = data.data.strategies;
            this.updateCallbacks.forEach(callback => callback(data));
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.ws = null;
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    onUpdate(callback: (data: WebSocketMessage) => void) {
        this.updateCallbacks.push(callback);
        return () => {
            const index = this.updateCallbacks.indexOf(callback);
            if (index !== -1) {
                this.updateCallbacks.splice(index, 1);
            }
        };
    }

    toggleStrategy(strategyId: number) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'toggle',
                data: { strategyId }
            }));
        }
    }
}

export const websocketService = new WebSocketService(); 