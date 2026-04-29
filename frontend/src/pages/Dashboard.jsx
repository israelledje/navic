import React, { useEffect, useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Overview from './Overview';
import Tracking from './Tracking';
import DeviceActivation from './DeviceActivation';
import DeviceSettings from './DeviceSettings';
import AdminDashboard from './AdminDashboard';
import api from '../api/api';
import './Dashboard.css';

const Dashboard = () => {
    const [user, setUser] = useState(null);

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const response = await api.get('/accounts/users/me/');
                setUser(response.data);
            } catch (err) {
                console.error('Failed to fetch user', err);
            }
        };
        fetchUser();
    }, []);

    return (
        <div className="dashboard-layout">
            <Sidebar user={user} />
            <main className="dashboard-main">
                <div className="dashboard-content no-header">
                    <Routes>
                        <Route path="overview" element={<Overview />} />
                        <Route path="tracking" element={<Tracking />} />
                        <Route path="activation" element={<DeviceActivation />} />
                        <Route path="settings" element={<DeviceSettings />} />
                        <Route path="admin" element={<AdminDashboard />} />
                        <Route path="/" element={<Overview />} />
                    </Routes>
                </div>
            </main>
        </div>
    );
};

export default Dashboard;
