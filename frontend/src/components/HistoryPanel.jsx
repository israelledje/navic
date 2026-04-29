import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, X, FastForward, SkipBack, Calendar, Clock, Download, ChevronRight } from 'lucide-react';
import api from '../api/api';
import './HistoryPanel.css';

const HistoryPanel = ({ device, onClose, onHistoryData, onPlaybackIndex, isPlaying, setIsPlaying }) => {
    const [startDate, setStartDate] = useState(() => {
        const d = new Date();
        d.setHours(0, 0, 0, 0);
        return d.toISOString().slice(0, 16); // YYYY-MM-DDThh:mm
    });
    
    const [endDate, setEndDate] = useState(() => {
        const d = new Date();
        d.setHours(23, 59, 59, 999);
        return d.toISOString().slice(0, 16);
    });

    const [loading, setLoading] = useState(false);
    const [historyPoints, setHistoryPoints] = useState([]);
    const [speedMultiplier, setSpeedMultiplier] = useState(1);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [stats, setStats] = useState({ distance: 0, maxSpeed: 0 });

    const playIntervalRef = useRef(null);

    // Fetch history
    const loadHistory = async () => {
        if (!device) return;
        setLoading(true);
        setIsPlaying(false);
        try {
            const sd = new Date(startDate).toISOString();
            const ed = new Date(endDate).toISOString();
            const response = await api.get(`/track/positions/path/?device_id=${device.id}&start_date=${sd}&end_date=${ed}`);
            const data = response.data;
            
            setHistoryPoints(data);
            onHistoryData(data);
            setCurrentIndex(0);
            onPlaybackIndex(0);
            
            // Calculer les stats de base
            let maxSpd = 0;
            data.forEach(p => { if (p.speed > maxSpd) maxSpd = p.speed; });
            setStats({ distance: data.length > 0 ? 'N/A' : 0, maxSpeed: Math.round(maxSpd) });
            
        } catch (error) {
            console.error('Erreur lors du chargement de l\'historique', error);
        } finally {
            setLoading(false);
        }
    };

    // Auto-load on mount
    useEffect(() => {
        loadHistory();
    }, [device.id]);

    // Playback logic
    useEffect(() => {
        if (isPlaying && historyPoints.length > 0) {
            playIntervalRef.current = setInterval(() => {
                setCurrentIndex(prev => {
                    if (prev >= historyPoints.length - 1) {
                        setIsPlaying(false);
                        return prev;
                    }
                    const next = prev + 1;
                    onPlaybackIndex(next);
                    return next;
                });
            }, 1000 / speedMultiplier); // 1 point par seconde, multiplié par la vitesse
        } else {
            clearInterval(playIntervalRef.current);
        }

        return () => clearInterval(playIntervalRef.current);
    }, [isPlaying, speedMultiplier, historyPoints]);

    const handleSeek = (e) => {
        const val = parseInt(e.target.value);
        setCurrentIndex(val);
        onPlaybackIndex(val);
    };

    const formatTimestamp = (isoString) => {
        if (!isoString) return '';
        const d = new Date(isoString);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    };

    const currentPoint = historyPoints[currentIndex];

    return (
        <div className="history-panel animate-slide-up">
            <div className="history-header">
                <h3>Historique : {device.vehicle_plate || device.name}</h3>
                <button className="close-btn" onClick={onClose}><X size={20} /></button>
            </div>

            <div className="history-filters">
                <div className="date-input">
                    <Calendar size={16} className="text-muted" />
                    <input 
                        type="datetime-local" 
                        value={startDate} 
                        onChange={e => setStartDate(e.target.value)} 
                    />
                </div>
                <ChevronRight size={16} className="text-muted mx-2" />
                <div className="date-input">
                    <Calendar size={16} className="text-muted" />
                    <input 
                        type="datetime-local" 
                        value={endDate} 
                        onChange={e => setEndDate(e.target.value)} 
                    />
                </div>
                <button className="btn-load" onClick={loadHistory} disabled={loading}>
                    {loading ? 'Chargement...' : 'Afficher'}
                </button>
            </div>

            {historyPoints.length > 0 ? (
                <div className="playback-container">
                    <div className="playback-controls">
                        <button className="control-btn" onClick={() => { setCurrentIndex(0); onPlaybackIndex(0); setIsPlaying(false); }}>
                            <SkipBack size={20} />
                        </button>
                        <button className="control-btn primary" onClick={() => setIsPlaying(!isPlaying)}>
                            {isPlaying ? <Pause size={20} /> : <Play size={20} />}
                        </button>
                        <div className="speed-control">
                            <FastForward size={16} />
                            <select value={speedMultiplier} onChange={(e) => setSpeedMultiplier(Number(e.target.value))}>
                                <option value={1}>x1</option>
                                <option value={2}>x2</option>
                                <option value={5}>x5</option>
                                <option value={10}>x10</option>
                                <option value={20}>x20</option>
                            </select>
                        </div>
                    </div>

                    <div className="progress-container">
                        <span className="time-display">{formatTimestamp(currentPoint?.timestamp)}</span>
                        <input 
                            type="range" 
                            min="0" 
                            max={historyPoints.length - 1} 
                            value={currentIndex} 
                            onChange={handleSeek}
                            className="progress-slider"
                        />
                        <span className="time-display">{formatTimestamp(historyPoints[historyPoints.length - 1]?.timestamp)}</span>
                    </div>

                    <div className="playback-stats">
                        <div className="stat-item">
                            <span className="label">Vitesse instant.</span>
                            <span className="value">{currentPoint ? Math.round(currentPoint.speed) : 0} km/h</span>
                        </div>
                        <div className="stat-item">
                            <span className="label">Vitesse max</span>
                            <span className="value">{stats.maxSpeed} km/h</span>
                        </div>
                        <div className="stat-item">
                            <span className="label">Points</span>
                            <span className="value">{currentIndex + 1} / {historyPoints.length}</span>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="no-data-msg">
                    {loading ? "Recherche des positions GPS..." : "Aucune donnée disponible pour cette période."}
                </div>
            )}
        </div>
    );
};

export default HistoryPanel;
