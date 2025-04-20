import { ref, onUnmounted } from 'vue';
import type { WebSocketMessage } from '@/types';

const ws = ref<WebSocket | null>(null);
const messageHandlers = ref<Set<(data: WebSocketMessage) => void>>(new Set());

export function useWebSocket() {
    const connect = () => {
        if (ws.value) return;

        ws.value = new WebSocket('ws://localhost:9001/ws');

        ws.value.onopen = () => {
            console.log('WebSocket connected');
        };

        ws.value.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data) as WebSocketMessage;
                messageHandlers.value.forEach(handler => handler(data));
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.value.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.value.onclose = () => {
            console.log('WebSocket disconnected');
            ws.value = null;
        };
    };

    const disconnect = () => {
        if (ws.value) {
            ws.value.close();
            ws.value = null;
        }
    };

    const onUpdate = (handler: (data: WebSocketMessage) => void) => {
        messageHandlers.value.add(handler);
        return () => messageHandlers.value.delete(handler);
    };

    const toggleStrategy = (strategyId: number) => {
        if (ws.value?.readyState === WebSocket.OPEN) {
            ws.value.send(JSON.stringify({
                type: 'toggle_strategy',
                strategyId
            }));
        }
    };

    // Cleanup on unmount
    onUnmounted(() => {
        disconnect();
        messageHandlers.value.clear();
    });

    return {
        connect,
        disconnect,
        onUpdate,
        toggleStrategy
    };
}

export const websocketService = useWebSocket(); 