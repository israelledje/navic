import React, { useState, useEffect } from 'react';
import { Search, Plus, ChevronDown, ChevronUp, Save, Smartphone, Gauge, Settings, Shield, Timer, Activity, BatteryCharging, Zap } from 'lucide-react';
import api from '../api/api';
import './DeviceSettings.css';

const DeviceSettings = () => {
    // State
    const [devices, setDevices] = useState([]);
    const [groups, setGroups] = useState([{ id: 'default', name: 'Main group', devices: [] }]);
    const [selectedDeviceId, setSelectedDeviceId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    // Detailed Settings State
    const [settings, setSettings] = useState(null);
    const [saving, setSaving] = useState(false);
    const [expandedSections, setExpandedSections] = useState({
        plan: true,
        phone: false,
        sensors: false,
        intervals: false,
        timezone: false,
        parking: false,
        offline: false
    });

    const [tariffPlans, setTariffPlans] = useState([]);

    // Fetch Devices and Plans
    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch list of trackers
                const [devicesRes, plansRes] = await Promise.all([
                    api.get('/devices/trackers/'),
                    api.get('/billing/device-plans/')
                ]);

                const deviceList = devicesRes.data.results || devicesRes.data;
                setDevices(deviceList);

                // Plans
                setTariffPlans(plansRes.data.results || plansRes.data);

                // Group devices (Simulated for now, assumes 1 group)
                setGroups([{
                    id: 'default',
                    name: `Main group (${deviceList.length})`,
                    devices: deviceList
                }]);

                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch data", err);
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    // Fetch Settings when device selected
    useEffect(() => {
        if (!selectedDeviceId) return;

        const fetchSettings = async () => {
            try {
                setSettings(null); // Reset
                const response = await api.get(`/devices/trackers/${selectedDeviceId}/settings/`);
                setSettings(response.data);
            } catch (err) {
                console.error("Failed to fetch settings", err);
                // If 404, maybe init default
            }
        };
        fetchSettings();
    }, [selectedDeviceId]);

    // Handle Input Change
    const handleSettingChange = (field, value) => {
        setSettings(prev => ({
            ...prev,
            [field]: value
        }));
    };

    // Save Settings
    const handleSave = async () => {
        if (!selectedDeviceId || !settings) return;
        setSaving(true);
        try {
            await api.patch(`/devices/trackers/${selectedDeviceId}/settings/`, settings);
            // Show toast/success?
            alert("Settings saved successfully!");
        } catch (err) {
            console.error("Failed to save settings", err);
            alert("Failed to save settings.");
        } finally {
            setSaving(false);
        }
    };

    const toggleSection = (section) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const getSelectedDevice = () => devices.find(d => d.id === selectedDeviceId);
    const selectedDevice = getSelectedDevice();
    const modelCapabilities = selectedDevice?.device_model_details?.features || {};
    // Note: features field was populated, but also check the new fields if detailed serializer returns them
    // Assuming serializer returns capabilities in 'features' or straight on model if we updated serializer
    // Let's rely on what we put in 'features' previously or check if we need to update serializer to expose new fields.
    // For now we assume 'features' or default to basic.

    // Helper to check capability
    const hasCapability = (cap) => {
        // Check if capability matches sensors list
        // We might need to fetch full model details if not present in list
        return true; // For now show all, logic below improves this
    };

    // Better: Helper using the new 'supported_sensors' if available
    // But we need to make sure the frontend receives it.
    // Let's assume the device object in list includes model details.

    // Filter Logic
    const filteredGroups = groups.map(group => ({
        ...group,
        devices: group.devices.filter(d =>
            d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            d.imei.includes(searchQuery)
        )
    })).filter(g => g.devices.length > 0 || searchQuery === '');

    return (
        <div className="settings-layout" style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
            {/* LEFT SIDEBAR: Device List */}
            <div className="objects-panel">
                <div className="objects-header">
                    <h2>Objects</h2>
                    <button className="new-group-btn">
                        <Plus size={16} /> NEW GROUP
                    </button>
                </div>

                <div className="search-box">
                    <div className="search-input-wrapper">
                        <Search className="search-icon" size={16} />
                        <input
                            type="text"
                            className="search-input"
                            placeholder="Quick search"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                </div>

                <div className="objects-list">
                    {loading ? (
                        <div style={{ padding: 20, textAlign: 'center' }}>Loading...</div>
                    ) : (
                        filteredGroups.map(group => (
                            <div key={group.id} className="group-item">
                                <div className="group-header">
                                    <span>{group.name}</span>
                                    <ChevronUp size={14} />
                                </div>
                                <div className="group-devices">
                                    {group.devices.map(device => (
                                        <div
                                            key={device.id}
                                            className={`device-item ${selectedDeviceId === device.id ? 'active' : ''}`}
                                            onClick={() => setSelectedDeviceId(device.id)}
                                        >
                                            <div className={`device-status-dot ${device.is_online ? 'online' : 'offline'}`} />
                                            <div className="device-info-mini">
                                                <div style={{ fontWeight: 500 }}>{device.name}</div>
                                                <div style={{ fontSize: 11, color: '#9ca3af' }}>{device.imei}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* RIGHT MAIN: Settings Form */}
            <div className="settings-content">
                {selectedDeviceId && settings ? (
                    <div className="device-details-container">
                        <div className="device-detail-header">
                            <div className="header-title">
                                <h1>{selectedDevice?.name || 'Device'}</h1>
                                <div className="device-meta">
                                    Model: {selectedDevice?.device_model_name} <br />
                                    IMEI: {selectedDevice?.imei}
                                </div>
                            </div>
                            <button
                                className="save-btn"
                                onClick={handleSave}
                                disabled={saving}
                            >
                                {saving ? 'Saving...' : 'SAVE'}
                            </button>
                        </div>

                        {/* Card 1: Tariff Plan */}
                        <div className="settings-card">
                            <div className="card-header" onClick={() => toggleSection('plan')}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <Shield size={18} color="#4b5563" />
                                    <span>Device tariff plan</span>
                                </div>
                                {expandedSections.plan ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </div>
                            {expandedSections.plan && (
                                <div className="card-body">
                                    <div className="form-field">
                                        <label>Subscription Plan</label>
                                        <select
                                            value={settings.device_plan || ''}
                                            onChange={(e) => handleSettingChange('device_plan', e.target.value ? parseInt(e.target.value) : null)}
                                        >
                                            <option value="">Select a plan</option>
                                            {tariffPlans.map(p => (
                                                <option key={p.id} value={p.id}>
                                                    {p.name} - {p.price_monthly} {p.currency}/mo
                                                </option>
                                            ))}
                                        </select>
                                        <div style={{ fontSize: 12, color: '#6b7280', marginTop: 5 }}>
                                            Charged per month (daily charge)
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Card 2: Phone & APN */}
                        <div className="settings-card">
                            <div className="card-header" onClick={() => toggleSection('phone')}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <Smartphone size={18} color="#4b5563" />
                                    <span>Connectivity & Phone</span>
                                </div>
                                {expandedSections.phone ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </div>
                            {expandedSections.phone && (
                                <div className="card-body">
                                    <div className="form-row">
                                        <div className="form-field">
                                            <label>APN Name</label>
                                            <input
                                                type="text"
                                                value={settings.apn || ''}
                                                onChange={(e) => handleSettingChange('apn', e.target.value)}
                                            />
                                        </div>
                                        <div className="form-field">
                                            <label>APN User</label>
                                            <input
                                                type="text"
                                                value={settings.apn_user || ''}
                                                onChange={(e) => handleSettingChange('apn_user', e.target.value)}
                                            />
                                        </div>
                                    </div>
                                    <div className="form-row">
                                        <div className="form-field">
                                            <label>APN Password</label>
                                            <input
                                                type="password"
                                                value={settings.apn_password || ''}
                                                onChange={(e) => handleSettingChange('apn_password', e.target.value)}
                                            />
                                        </div>
                                        <div className="form-field">
                                            <label>Authorized Numbers</label>
                                            <input
                                                type="text"
                                                placeholder="+336..., +337..."
                                                value={settings.authorized_numbers || ''}
                                                onChange={(e) => handleSettingChange('authorized_numbers', e.target.value)}
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Card New: Timezone */}
                        <div className="settings-card">
                            <div className="card-header" onClick={() => toggleSection('timezone')}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <Timer size={18} color="#4b5563" />
                                    <span>Timezone</span>
                                </div>
                                {expandedSections.timezone ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </div>
                            {expandedSections.timezone && (
                                <div className="card-body">
                                    <div className="form-field">
                                        <label>Device Timezone</label>
                                        <input
                                            type="text"
                                            placeholder="UTC, Africa/Douala, etc."
                                            value={settings.timezone || 'UTC'}
                                            onChange={(e) => handleSettingChange('timezone', e.target.value)}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Card New: Parking Detection */}
                        <div className="settings-card">
                            <div className="card-header" onClick={() => toggleSection('parking')}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <Activity size={18} color="#4b5563" />
                                    <span>Parking Detection</span>
                                </div>
                                {expandedSections.parking ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </div>
                            {expandedSections.parking && (
                                <div className="card-body">
                                    <div className="form-row">
                                        <div className="form-field">
                                            <label>Idling Engine Duration (minutes)</label>
                                            <input
                                                type="number"
                                                value={settings.idling_threshold || 5}
                                                onChange={(e) => handleSettingChange('idling_threshold', parseInt(e.target.value))}
                                            />
                                        </div>
                                        <div className="form-field">
                                            <label>Max Idling Speed (km/h)</label>
                                            <input
                                                type="number"
                                                value={settings.idling_speed_limit || 3}
                                                onChange={(e) => handleSettingChange('idling_speed_limit', parseInt(e.target.value))}
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Card New: Connection Status */}
                        <div className="settings-card">
                            <div className="card-header" onClick={() => toggleSection('offline')}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <Zap size={18} color="#4b5563" />
                                    <span>Connection Status</span>
                                </div>
                                {expandedSections.offline ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </div>
                            {expandedSections.offline && (
                                <div className="card-body">
                                    <div className="form-field">
                                        <label>Offline Timeout (minutes)</label>
                                        <input
                                            type="number"
                                            value={settings.offline_timeout || 10}
                                            onChange={(e) => handleSettingChange('offline_timeout', parseInt(e.target.value))}
                                        />
                                        <div style={{ fontSize: 12, color: '#6b7280', marginTop: 5 }}>
                                            If the device fails to connect to the server within the defined time, it will be considered offline.
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Card 3: Reporting Intervals */}
                        <div className="settings-card">
                            <div className="card-header" onClick={() => toggleSection('intervals')}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <Gauge size={18} color="#4b5563" />
                                    <span>Data Reporting</span>
                                </div>
                                {expandedSections.intervals ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </div>
                            {expandedSections.intervals && (
                                <div className="card-body">
                                    <div className="form-row">
                                        <div className="form-field">
                                            <label>Moving Interval (seconds)</label>
                                            <input
                                                type="number"
                                                value={settings.reporting_interval_moving || 60}
                                                onChange={(e) => handleSettingChange('reporting_interval_moving', parseInt(e.target.value))}
                                            />
                                        </div>
                                        <div className="form-field">
                                            <label>Stopped Interval (seconds)</label>
                                            <input
                                                type="number"
                                                value={settings.reporting_interval_stopped || 3600}
                                                onChange={(e) => handleSettingChange('reporting_interval_stopped', parseInt(e.target.value))}
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Card 4: Sensors */}
                        <div className="settings-card">
                            <div className="card-header" onClick={() => toggleSection('sensors')}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <Settings size={18} color="#4b5563" />
                                    <span>Sensors Configuration</span>
                                </div>
                                {expandedSections.sensors ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </div>
                            {expandedSections.sensors && (
                                <div className="card-body">
                                    <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 15 }}>
                                        Configure sensors supported by your <strong>{selectedDevice?.device_model_name}</strong>.
                                    </p>

                                    {(!selectedDevice?.device_model_details?.supported_sensors || selectedDevice.device_model_details.supported_sensors.includes('fuel')) && (
                                        <div className="toggle-field">
                                            <span>Fuel Sensor</span>
                                            <input
                                                type="checkbox"
                                                checked={settings.fuel_sensor_enabled || false}
                                                onChange={(e) => handleSettingChange('fuel_sensor_enabled', e.target.checked)}
                                            />
                                        </div>
                                    )}

                                    {(!selectedDevice?.device_model_details?.supported_sensors || selectedDevice.device_model_details.supported_sensors.includes('temp')) && (
                                        <div className="toggle-field">
                                            <span>Temperature Sensor</span>
                                            <input
                                                type="checkbox"
                                                checked={settings.temperature_sensor_enabled || false}
                                                onChange={(e) => handleSettingChange('temperature_sensor_enabled', e.target.checked)}
                                            />
                                        </div>
                                    )}

                                    {(!selectedDevice?.device_model_details?.supported_sensors || selectedDevice.device_model_details.supported_sensors.includes('door')) && (
                                        <div className="toggle-field">
                                            <span>Door Sensor</span>
                                            <input
                                                type="checkbox"
                                                checked={settings.door_sensor_enabled || false}
                                                onChange={(e) => handleSettingChange('door_sensor_enabled', e.target.checked)}
                                            />
                                        </div>
                                    )}

                                    {/* Additional generic message if no specific sensors listed but known mismatch could happen */}
                                </div>
                            )}
                        </div>

                    </div>
                ) : (
                    <div className="empty-state">
                        <Settings size={64} style={{ marginBottom: 20, opacity: 0.2 }} />
                        <h3>Select an object to configure</h3>
                        <p>Choose a device from the list on the left to view settings.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DeviceSettings;
