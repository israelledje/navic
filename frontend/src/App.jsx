import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { createContext, useState, useEffect } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import api from './api/api';

const queryClient = new QueryClient();

export const ThemeContext = createContext({
    platformName: 'Navic',
    logo: null,
    primaryColor: '#00cc99'
});

const ProtectedRoute = ({ children }) => {
    const isAuthenticated = !!localStorage.getItem('access_token');
    return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
    const [themeConfig, setThemeConfig] = useState({
        platformName: 'Navic',
        logo: null,
        primaryColor: '#00cc99'
    });

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const domain = window.location.hostname;
                const response = await api.get(`/settings/public/?domain=${domain}`);
                const data = response.data;
                
                setThemeConfig({
                    platformName: data.platform_name || 'Navic',
                    logo: data.logo,
                    primaryColor: data.primary_color || '#00cc99'
                });

                if (data.primary_color) {
                    document.documentElement.style.setProperty('--primary-color', data.primary_color);
                }
                
                if (data.favicon) {
                    let link = document.querySelector("link[rel~='icon']");
                    if (!link) {
                        link = document.createElement('link');
                        link.rel = 'icon';
                        document.head.appendChild(link);
                    }
                    link.href = data.favicon;
                }
                
                document.title = data.platform_name || 'Navic';
            } catch (err) {
                console.error('Failed to load public settings', err);
            }
        };
        fetchSettings();
    }, []);

    return (
        <ThemeContext.Provider value={themeConfig}>
            <QueryClientProvider client={queryClient}>
                <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
                    <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route
                            path="/dashboard/*"
                            element={
                                <ProtectedRoute>
                                    <Dashboard />
                                </ProtectedRoute>
                            }
                        />
                        <Route path="/" element={<Navigate to="/dashboard" />} />
                    </Routes>
                </Router>
            </QueryClientProvider>
        </ThemeContext.Provider>
    );
}

export default App;
