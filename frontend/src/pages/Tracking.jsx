import React, { useState, useEffect } from 'react';
import {
    Search, Filter, List, MoreVertical,
    MapPin, Clock, Gauge, Zap,
    ChevronDown, ChevronUp, History, Info as InfoIcon,
    X, Settings, Lock, Star, RotateCcw
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import api from '../api/api';
import './Tracking.css';
import { useTrackingSocket } from '../hooks/useTrackingSocket';
import HistoryPanel from '../components/HistoryPanel';

// Fix for leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const DeviceItem = ({ device, onSelect, onShowDetails, onShowHistory, isSelected }) => {
    const [isHovered, setIsHovered] = useState(false);

    return (
        <div
            className={`device-item ${isSelected ? 'selected' : ''}`}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            onClick={() => onSelect(device)}
        >
            <div className="device-checkbox">
                <input type="checkbox" checked={isSelected} readOnly />
            </div>
            <div className="device-icon">
                <div className={`status-icon ${device.is_online ? 'online' : 'offline'}`}>
                    <Zap size={16} />
                </div>
            </div>
            <div className="device-info">
                <div className="device-name">{device.vehicle_plate || device.name}</div>
                <div className="device-status">
                    <span className={`status-dot ${device.is_online ? 'bg-green' : 'bg-red'}`}></span>
                    {device.is_online ? 'En ligne' : 'Hors-ligne'} • {device.last_connection_human || 'Non disponible'}
                </div>
            </div>
            {isHovered && (
                <div className="device-actions">
                    <button className="action-btn" onClick={(e) => { e.stopPropagation(); onShowHistory(device); }}>
                        <History size={16} />
                    </button>
                    <button className="action-btn detail-trigger" onClick={(e) => { e.stopPropagation(); onShowDetails(device); }}>
                        <InfoIcon size={16} />
                    </button>
                </div>
            )}
        </div>
    );
};

const DetailSection = ({ title, children, isOpen, onToggle }) => (
    <div className="detail-section">
        <div className="detail-section-header" onClick={onToggle}>
            <h4>{title}</h4>
            {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </div>
        {isOpen && <div className="detail-section-content">{children}</div>}
    </div>
);

const DeviceDetailPanel = ({ device, onClose }) => {
    const [openSections, setOpenSections] = useState({
        emplacement: true,
        statut: true,
        odometer: true,
        moteur: true,
        obd: true,
        sensors: true,
        inputs: true,
        outputs: true,
        driver: true,
        events: true,
        gps: true
    });

    const toggleSection = (section) => {
        setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
    };

    if (!device) return null;

    return (
        <div className="detail-panel animate-fade-in">
            <div className="detail-panel-header">
                <div className="detail-header-content">
                    <div className="detail-title-row">
                        <h3>{device.vehicle_plate || device.name}</h3>
                        <div className="header-actions">
                            <Lock size={18} />
                            <Settings size={18} />
                            <X size={18} className="close-btn" onClick={onClose} />
                        </div>
                    </div>
                    <div className="detail-subtitle">
                        <span className="time"><Clock size={14} /> {device.last_connection_human || '2d 2h 38m'}</span>
                        <span className="gps-status"><Zap size={14} className="text-green" /> GPS mis à jour</span>
                    </div>
                </div>
                <div className="street-view-placeholder">
                    <div className="street-view-overlay">
                        <MapPin size={24} />
                        <span>Vue rue</span>
                    </div>
                    <Star size={20} className="star-icon" />
                </div>
            </div>

            <div className="detail-panel-scroll">
                <DetailSection
                    title="Emplacement"
                    isOpen={openSections.emplacement}
                    onToggle={() => toggleSection('emplacement')}
                >
                    <div className="info-row">
                        <MapPin size={18} className="text-muted" />
                        <div className="info-content">
                            <p>Yaoundé, Centre, Cameroun</p>
                            <small>{device.last_position?.latitude}, {device.last_position?.longitude}</small>
                        </div>
                        <RotateCcw size={16} className="text-blue cursor-pointer" />
                    </div>
                </DetailSection>

                <DetailSection
                    title="Statut"
                    isOpen={openSections.statut}
                    onToggle={() => toggleSection('statut')}
                >
                    <div className="info-row">
                        <div className="status-indicator">P</div>
                        <div className="info-content">
                            <p>Arrêté</p>
                            <small>Depuis 2d 2h 38m</small>
                        </div>
                        <Star size={16} className="text-muted" />
                    </div>
                </DetailSection>

                <DetailSection
                    title="Compteur kilométrique"
                    isOpen={openSections.odometer}
                    onToggle={() => toggleSection('odometer')}
                >
                    <div className="info-row">
                        <Gauge size={18} className="text-muted" />
                        <div className="info-content">
                            <p>{device.last_position?.odometer || '0'} km</p>
                        </div>
                    </div>
                </DetailSection>

                <DetailSection
                    title="Heures moteur"
                    isOpen={openSections.moteur}
                    onToggle={() => toggleSection('moteur')}
                >
                    <div className="info-row">
                        <Clock size={18} className="text-muted" />
                        <div className="info-content">
                            <p>{device.last_position?.engine_hours || '0'} heures</p>
                        </div>
                    </div>
                </DetailSection>

                <DetailSection
                    title="OBD2 & CanBus"
                    isOpen={openSections.obd}
                    onToggle={() => toggleSection('obd')}
                >
                    <p className="no-data">Aucune donnée</p>
                </DetailSection>

                <DetailSection
                    title="Lectures du capteur"
                    isOpen={openSections.sensors}
                    onToggle={() => toggleSection('sensors')}
                >
                    <div className="info-row">
                        <Zap size={18} className="text-muted" />
                        <div className="info-content">
                            <p>Tension d'alimentation</p>
                            <small>{device.last_position?.external_power || 'N/A'} V</small>
                        </div>
                    </div>
                </DetailSection>

                <DetailSection
                    title="Appareil GPS"
                    isOpen={openSections.gps}
                    onToggle={() => toggleSection('gps')}
                >
                    <div className="gps-details-grid">
                        <div className="gps-detail-item">
                            <div className={`dot ${device.is_online ? 'bg-green' : 'bg-red'}`}></div>
                            <span>{device.is_online ? 'Connecté' : 'Déconnecté'}</span>
                        </div>
                        <div className="gps-detail-item">
                            <Zap size={16} className="text-green" />
                            <span>Batterie: {device.last_position?.battery_level || '0'}%</span>
                        </div>
                        <div className="gps-detail-item">
                            <div className="signal-bars">
                                <div className={`bar ${device.last_position?.signal >= 30 ? 'filled' : ''}`}></div>
                                <div className={`bar ${device.last_position?.signal >= 60 ? 'filled' : ''}`}></div>
                                <div className={`bar ${device.last_position?.signal >= 90 ? 'filled' : ''}`}></div>
                            </div>
                            <span>Signal: {device.last_position?.signal || '0'}%</span>
                        </div>
                    </div>
                </DetailSection>

                <div className="model-info">
                    <InfoIcon size={18} className="text-muted" />
                    <div>
                        <p>Modèle: {device.device_model_name || 'Teltonika FMB920'}</p>
                        <small>ID: {device.imei}</small>
                    </div>
                </div>
            </div>
        </div>
    );
};

const MapUpdater = ({ center }) => {
    const map = useMap();
    useEffect(() => {
        if (center) map.setView(center, map.getZoom());
    }, [center, map]);
    return null;
};

const Tracking = () => {
    const [devices, setDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [showDetailPanel, setShowDetailPanel] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    
    // États pour l'historique
    const [showHistoryPanel, setShowHistoryPanel] = useState(false);
    const [historyData, setHistoryData] = useState([]);
    const [playbackIndex, setPlaybackIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);

    const { lastUpdate, isConnected } = useTrackingSocket('user');

    useEffect(() => {
        const fetchDevices = async () => {
            try {
                const response = await api.get('/devices/trackers/');
                const data = Array.isArray(response.data) ? response.data : response.data.results;

                if (data) {
                    const mapped = data.map(d => ({
                        ...d,
                        last_connection_human: d.last_connection ? new Date(d.last_connection).toLocaleString() : 'Jamais'
                    }));
                    setDevices(mapped);
                }
            } catch (err) {
                console.error('Failed to fetch devices', err);
            }
        };
        fetchDevices();
    }, []);

    // Gérer les mises à jour en temps réel
    useEffect(() => {
        if (!lastUpdate) return;

        const { type, data } = lastUpdate;

        if (type === 'initial_positions') {
            setDevices(prevDevices => {
                const updated = [...prevDevices];
                data.forEach(wsDevice => {
                    const index = updated.findIndex(d => d.id === wsDevice.device_id);
                    if (index !== -1) {
                        updated[index] = {
                            ...updated[index],
                            last_position: {
                                latitude: wsDevice.latitude,
                                longitude: wsDevice.longitude,
                                speed: wsDevice.speed,
                                timestamp: wsDevice.timestamp,
                                ignition: wsDevice.ignition,
                                battery_level: wsDevice.battery_level,
                                odometer: wsDevice.odometer,
                                external_power: wsDevice.external_power,
                                signal: wsDevice.signal
                            },
                            is_online: wsDevice.is_online,
                            last_connection: wsDevice.timestamp,
                            last_connection_human: new Date(wsDevice.timestamp).toLocaleString()
                        };
                    }
                });
                return updated;
            });
        } else if (type === 'position_update') {
            setDevices(prevDevices => {
                const index = prevDevices.findIndex(d => d.id === data.device_id);
                if (index === -1) return prevDevices;

                const updated = [...prevDevices];
                updated[index] = {
                    ...updated[index],
                    last_position: {
                        latitude: data.latitude,
                        longitude: data.longitude,
                        speed: data.speed,
                        timestamp: data.timestamp,
                        ignition: data.ignition,
                        battery_level: data.battery_level,
                        odometer: data.odometer,
                        external_power: data.external_power,
                        signal: data.signal
                    },
                    is_online: data.is_online,
                    last_connection: data.timestamp,
                    last_connection_human: new Date(data.timestamp).toLocaleString()
                };

                // Si c'est l'appareil sélectionné, le mettre à jour aussi
                if (selectedDevice && selectedDevice.id === data.device_id) {
                    // On évite une boucle infinie en ne mettant à jour que si les données ont changé
                    // mais ici setSelectedDevice(updated[index]) est sûr car updated[index] est un nouvel objet
                }

                return updated;
            });
        }
    }, [lastUpdate]);

    // Synchroniser selectedDevice quand les devices changent
    useEffect(() => {
        if (selectedDevice) {
            const updated = devices.find(d => d.id === selectedDevice.id);
            if (updated && JSON.stringify(updated.last_position) !== JSON.stringify(selectedDevice.last_position)) {
                setSelectedDevice(updated);
            }
        }
    }, [devices, selectedDevice]);

    const filteredDevices = devices.filter(d =>
        d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (d.vehicle_plate && d.vehicle_plate.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
        <div className="tracking-page">
            <div className="tracking-sidebar">
                <div className="sidebar-list-header">
                    <div className="list-title">
                        <List size={18} />
                        <h2>Traqueurs</h2>
                        <div className="header-icons">
                            <Filter size={18} />
                            <List size={18} />
                            <MoreVertical size={18} />
                        </div>
                    </div>
                    <div className="search-box">
                        <input
                            type="text"
                            placeholder="Recherche rapide"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                        <Search size={18} className="search-icon" />
                    </div>
                </div>

                <div className="list-group">
                    <div className="group-header">
                        <input type="checkbox" />
                        <div className="group-color-box"></div>
                        <span>Groupe principal ({filteredDevices.length}/{devices.length})</span>
                        <ChevronUp size={16} />
                    </div>
                    <div className="device-list">
                        {filteredDevices.map(device => (
                            <DeviceItem
                                key={device.id}
                                device={device}
                                isSelected={selectedDevice?.id === device.id}
                                onSelect={(d) => {
                                    setSelectedDevice(d);
                                    setShowDetailPanel(false);
                                    setShowHistoryPanel(false);
                                }}
                                onShowDetails={(d) => {
                                    setSelectedDevice(d);
                                    setShowHistoryPanel(false);
                                    setShowDetailPanel(true);
                                }}
                                onShowHistory={(d) => {
                                    setSelectedDevice(d);
                                    setShowDetailPanel(false);
                                    setShowHistoryPanel(true);
                                }}
                            />
                        ))}
                    </div>
                </div>
            </div>

            <div className="map-container">
                <MapContainer
                    center={[3.848, 11.502]}
                    zoom={13}
                    style={{ height: '100%', width: '100%' }}
                    zoomControl={false}
                >
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />
                    {!showHistoryPanel && devices.map(device => (
                        device.last_position?.latitude && (
                            <Marker
                                key={device.id}
                                position={[device.last_position.latitude, device.last_position.longitude]}
                                onClick={() => { setSelectedDevice(device); setShowHistoryPanel(false); setShowDetailPanel(true); }}
                            >
                                <Popup>
                                    <strong>{device.vehicle_plate || device.name}</strong><br />
                                    Vitesse: {device.last_position.speed || 0} km/h
                                </Popup>
                            </Marker>
                        )
                    ))}

                    {/* History Polyline and Marker */}
                    {showHistoryPanel && historyData.length > 0 && (
                        <>
                            <Polyline 
                                positions={historyData.map(p => [p.latitude, p.longitude])} 
                                color="#00cc99" 
                                weight={4} 
                                opacity={0.7} 
                            />
                            {historyData[playbackIndex] && (
                                <Marker 
                                    position={[historyData[playbackIndex].latitude, historyData[playbackIndex].longitude]}
                                    zIndexOffset={1000}
                                >
                                    <Popup>
                                        <strong>{selectedDevice?.vehicle_plate || selectedDevice?.name} (Historique)</strong><br />
                                        Vitesse: {Math.round(historyData[playbackIndex].speed)} km/h<br />
                                        Heure: {new Date(historyData[playbackIndex].timestamp).toLocaleTimeString()}
                                    </Popup>
                                </Marker>
                            )}
                            <MapUpdater center={historyData[playbackIndex] ? [historyData[playbackIndex].latitude, historyData[playbackIndex].longitude] : null} />
                        </>
                    )}

                    {!showHistoryPanel && selectedDevice?.last_position?.latitude && (
                        <MapUpdater center={[selectedDevice.last_position.latitude, selectedDevice.last_position.longitude]} />
                    )}
                </MapContainer>

                <div className="map-controls">
                    <div className="control-btn"><Search size={20} /></div>
                    <div className="control-btn"><MapPin size={20} /></div>
                    <div className="control-btn"><Layers size={20} /></div>
                </div>

                {showDetailPanel && selectedDevice && !showHistoryPanel && (
                    <DeviceDetailPanel
                        device={selectedDevice}
                        onClose={() => setShowDetailPanel(false)}
                    />
                )}
                
                {showHistoryPanel && selectedDevice && (
                    <HistoryPanel
                        device={selectedDevice}
                        onClose={() => setShowHistoryPanel(false)}
                        onHistoryData={setHistoryData}
                        onPlaybackIndex={setPlaybackIndex}
                        isPlaying={isPlaying}
                        setIsPlaying={setIsPlaying}
                    />
                )}
            </div>
        </div>
    );
};

const Layers = ({ size }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
        <polyline points="2 17 12 22 22 17"></polyline>
        <polyline points="2 12 12 17 22 12"></polyline>
    </svg>
);

export default Tracking;
