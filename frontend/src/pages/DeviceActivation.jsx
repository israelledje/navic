import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ChevronRight, ChevronDown, Check, X } from 'lucide-react';
import api from '../api/api';
import './DeviceActivation.css';

const DeviceActivation = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);

    // Form Data
    const [objectName, setObjectName] = useState('');
    const [selectedModel, setSelectedModel] = useState(null);
    const [imei, setImei] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [apn, setApn] = useState('');
    const [apnUsername, setApnUsername] = useState('');
    const [apnPassword, setApnPassword] = useState('');
    const [activationCode, setActivationCode] = useState('');

    // Model Selection State
    const [models, setModels] = useState([]);
    const [manufacturers, setManufacturers] = useState({});
    const [searchQuery, setSearchQuery] = useState('');
    const [expandedManu, setExpandedManu] = useState({}); // { "Coban": true }

    // Loading State
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Fetch models on mount
    useEffect(() => {
        const fetchModels = async () => {
            try {
                // In a real scenario, this would support pagination or a lightweight list endpoint
                const response = await api.get('/devices/models/');
                const data = response.data.results || response.data;
                setModels(data);

                // Group by manufacturer
                const grouped = {};
                data.forEach(model => {
                    const manu = model.manufacturer || 'Unknown';
                    if (!grouped[manu]) {
                        grouped[manu] = [];
                    }
                    grouped[manu].push(model);
                });
                setManufacturers(grouped);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch device models", err);
                setError("Could not load device models. Please try again.");
                setLoading(false);
            }
        };
        fetchModels();
    }, []);

    // Filter logic
    const getFilteredManufacturers = () => {
        if (!searchQuery) return manufacturers;

        const filtered = {};
        const query = searchQuery.toLowerCase();

        Object.keys(manufacturers).forEach(manu => {
            const manuModels = manufacturers[manu];
            // Check if manufacturer name matches OR any of its models match
            const manuMatch = manu.toLowerCase().includes(query);
            const matchingModels = manuModels.filter(m => m.name.toLowerCase().includes(query));

            if (manuMatch || matchingModels.length > 0) {
                // If manufacturer matches, show all (or just matching models? usually all or matching)
                // Let's show only matching models if manufacturer doesn't match effectively
                filtered[manu] = manuMatch ? manuModels : matchingModels;
            }
        });

        return filtered;
    };

    const toggleManufacturer = (manu) => {
        setExpandedManu(prev => ({
            ...prev,
            [manu]: !prev[manu]
        }));
    };

    const handleModelSelect = (model) => {
        setSelectedModel(model);
        // Auto-expand if needed handled by logic, but selecting usually collapses search or just highlights
        setSearchQuery(''); // Clear search on select? Optional.
    };

    const clearSelection = () => {
        setSelectedModel(null);
    };

    const handleSubmit = async () => {
        setLoading(true);
        setError('');

        try {
            // 1. Create Device
            const devicePayload = {
                name: objectName,
                imei: imei,
                device_model: selectedModel.id,
                status: 'active',
                // Default constraints
                update_interval: 60,
            };

            const deviceRes = await api.post('/devices/trackers/', devicePayload);
            const newDevice = deviceRes.data;

            // 2. Save Settings (APN, etc)
            // Note: Currently devices/create might not handle settings inline depending on backend.
            // If backend supports nested settings, great. If not, we patch settings.
            if (apn || phoneNumber) {
                await api.patch(`/devices/trackers/${newDevice.id}/settings/`, {
                    apn: apn,
                    apn_user: apnUsername,
                    apn_password: apnPassword,
                    // custom_settings: { phone_number: phoneNumber } // If backend supports
                });
            }

            navigate('/dashboard/tracking');
        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                // Formatting error errors
                const errors = Object.entries(err.response.data)
                    .map(([key, val]) => `${key}: ${val}`)
                    .join(', ');
                setError(errors || 'Activation failed');
            } else {
                setError('Activation failed. Please check your connection.');
            }
        } finally {
            setLoading(false);
        }
    };

    const filteredManufacturers = getFilteredManufacturers();

    return (
        <div className="activation-container">
            <div className="activation-wizard">
                <div className="wizard-header">
                    Device activation {step === 1 ? '- Step 1/2' : '- Step 2/2'}
                </div>

                <div className="wizard-content">
                    {error && <div style={{ color: '#ff6b6b', marginBottom: '10px' }}>{error}</div>}

                    {step === 1 && (
                        <>
                            <div className="form-group">
                                <label>Choose object name <span className="required-star">*</span></label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="e.g. Truck 01"
                                    value={objectName}
                                    onChange={e => setObjectName(e.target.value)}
                                />
                            </div>

                            <div className="form-group">
                                <label>Select device model <span className="required-star">*</span></label>

                                {selectedModel ? (
                                    <div className="selected-model-display" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: '#2d333b', borderRadius: '4px', border: '1px solid #3e454d', marginBottom: '10px' }}>
                                        <div className="selected-model-info">
                                            <div style={{ fontWeight: 'bold', color: '#fff' }}>{selectedModel.manufacturer} {selectedModel.name}</div>
                                            {selectedModel.supported_features && selectedModel.supported_features.length > 0 && (
                                                <div className="model-features" style={{ fontSize: '0.85rem', color: '#8b949e', marginTop: '4px' }}>
                                                    Fonctionnalités : {selectedModel.supported_features.join(', ')}
                                                </div>
                                            )}
                                        </div>
                                        <X size={16} className="remove-selection" onClick={clearSelection} style={{ cursor: 'pointer', color: '#ff6b6b' }} />
                                    </div>
                                ) : (
                                    <>
                                        <div className="model-search-container">
                                            <input
                                                type="text"
                                                className="model-search-input"
                                                placeholder="Quick Search (e.g. 303)"
                                                value={searchQuery}
                                                onChange={(e) => {
                                                    setSearchQuery(e.target.value);
                                                    // Auto-expand all if searching
                                                    if (e.target.value) {
                                                        const allOpen = {};
                                                        Object.keys(manufacturers).forEach(m => allOpen[m] = true);
                                                        setExpandedManu(allOpen);
                                                    }
                                                }}
                                            />
                                            <button className="model-search-btn">
                                                <Search size={14} />
                                            </button>
                                        </div>

                                        <div className="manufacturers-list">
                                            {loading ? <div style={{ padding: '10px' }}>Loading models...</div> :
                                                Object.keys(filteredManufacturers).length === 0 ? <div style={{ padding: '10px' }}>No models found.</div> :
                                                    Object.keys(filteredManufacturers).map(manu => (
                                                        <div key={manu} className="manufacturer-item">
                                                            <div
                                                                className="manufacturer-header"
                                                                onClick={() => toggleManufacturer(manu)}
                                                            >
                                                                <span>
                                                                    {expandedManu[manu] ? <ChevronDown size={14} style={{ marginRight: 5 }} /> : <ChevronRight size={14} style={{ marginRight: 5 }} />}
                                                                    {manu}
                                                                </span>
                                                                <span className="model-count">{filteredManufacturers[manu].length}</span>
                                                            </div>

                                                            {expandedManu[manu] && (
                                                                <div className="models-sublist">
                                                                    {filteredManufacturers[manu].map(model => (
                                                                        <div
                                                                            key={model.id}
                                                                            className="model-item"
                                                                            onClick={() => handleModelSelect(model)}
                                                                        >
                                                                            {model.name}
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    ))}
                                        </div>
                                    </>
                                )}
                            </div>
                        </>
                    )}

                    {step === 2 && (
                        <>
                            <div className="form-group">
                                <label>Phone number (SIM card)</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="+33..."
                                    value={phoneNumber}
                                    onChange={e => setPhoneNumber(e.target.value)}
                                />
                            </div>

                            <div className="form-group" style={{ border: '1px solid #3e454d', padding: '10px', borderRadius: '4px' }}>
                                <label style={{ fontWeight: 'bold', color: '#fff' }}>GPRS settings</label>
                                <div style={{ marginTop: '10px' }}>
                                    <label>APN <span className="required-star">*</span></label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="internet"
                                        value={apn}
                                        onChange={e => setApn(e.target.value)}
                                    />
                                </div>
                                <div style={{ marginTop: '10px' }}>
                                    <label>Username</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        value={apnUsername}
                                        onChange={e => setApnUsername(e.target.value)}
                                    />
                                </div>
                                <div style={{ marginTop: '10px' }}>
                                    <label>Password</label>
                                    <input
                                        type="password"
                                        className="form-input"
                                        value={apnPassword}
                                        onChange={e => setApnPassword(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Device ID (IMEI) <span className="required-star">*</span></label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="15 digits"
                                    maxLength={15}
                                    value={imei}
                                    onChange={e => {
                                        const val = e.target.value.replace(/[^0-9]/g, '');
                                        setImei(val);
                                    }}
                                />
                            </div>

                            <div className="form-group">
                                <label>Activation code</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="Optional"
                                    value={activationCode}
                                    onChange={e => setActivationCode(e.target.value)}
                                />
                            </div>
                        </>
                    )}
                </div>

                <div className="wizard-footer">
                    {step === 1 ? (
                        <>
                            <button className="btn btn-secondary" onClick={() => navigate('/dashboard/overview')}>Cancel</button>
                            <button
                                className="btn btn-primary"
                                disabled={!selectedModel || !objectName}
                                onClick={() => setStep(2)}
                            >
                                Next step
                            </button>
                        </>
                    ) : (
                        <>
                            <button className="btn btn-secondary" onClick={() => setStep(1)}>Back</button>
                            <button
                                className="btn btn-primary"
                                disabled={!imei || !apn || loading}
                                onClick={handleSubmit}
                            >
                                {loading ? 'Activating...' : 'Activate Device'}
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DeviceActivation;
