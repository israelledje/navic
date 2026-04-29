import { useEffect, useRef, useState, useCallback } from 'react';

const SOCKET_URL = 'ws://127.0.0.1:8000/ws/tracking';

/**
 * Hook pour gérer la connexion WebSocket de tracking
 * @param {string} type 'user' ou 'device'
 * @param {string|number} id ID du device (optionnel si type 'user')
 */
export const useTrackingSocket = (type = 'user', id = null) => {
    const [lastUpdate, setLastUpdate] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const socketRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    const connect = useCallback(() => {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        // Fermer la connexion existante si elle existe
        if (socketRef.current) {
            socketRef.current.close();
        }

        const url = type === 'user'
            ? `${SOCKET_URL}/user/?token=${token}`
            : `${SOCKET_URL}/${id}/?token=${token}`;

        const ws = new WebSocket(url);

        ws.onopen = () => {
            console.log(`[WS] Connecté au tracking ${type}`);
            setIsConnected(true);
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
                reconnectTimeoutRef.current = null;
            }
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                setLastUpdate(data);
            } catch (err) {
                console.error('[WS] Erreur parsing message:', err);
            }
        };

        ws.onclose = (e) => {
            console.log(`[WS] Déconnecté du tracking ${type}. Code: ${e.code}`);
            setIsConnected(false);

            // Tentative de reconnexion après 3 secondes si ce n'est pas une fermeture normale
            if (e.code !== 1000) {
                reconnectTimeoutRef.current = setTimeout(() => {
                    console.log('[WS] Tentative de reconnexion...');
                    connect();
                }, 3000);
            }
        };

        ws.onerror = (err) => {
            console.error('[WS] Erreur:', err);
            ws.close();
        };

        socketRef.current = ws;
    }, [type, id]);

    useEffect(() => {
        connect();

        return () => {
            if (socketRef.current) {
                socketRef.current.close(1000); // Fermeture normale
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [connect]);

    const sendMessage = useCallback((message) => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify(message));
        }
    }, []);

    return { lastUpdate, isConnected, sendMessage };
};
