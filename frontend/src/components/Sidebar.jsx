import React, { useContext } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
    BarChart3, Map, Share2, FilePieChart,
    Truck, Users, Bell, MessageSquare,
    Settings, Info, Power, ChevronRight,
    UserCircle
} from 'lucide-react';
import { ThemeContext } from '../App';
import './Sidebar.css';

const Sidebar = ({ user }) => {
    const navigate = useNavigate();
    const { platformName, logo } = useContext(ThemeContext);

    const handleLogout = () => {
        localStorage.clear();
        navigate('/login');
    };

    const menuItems = [
        { icon: BarChart3, label: 'Overview', path: '/dashboard/overview' },
        { icon: Map, label: 'Tracking', path: '/dashboard/tracking' },
        { icon: Share2, label: 'Geo links', path: '/dashboard/geo-links' },
        { icon: FilePieChart, label: 'Reports', path: '/dashboard/reports' },
        { icon: Truck, label: 'Fleet management', path: '/dashboard/fleet' },
        { icon: Users, label: 'Field service', path: '/dashboard/field-service' },
    ];

    const bottomItems = [
        { icon: Bell, label: 'Alerts', path: '/dashboard/alerts' },
        { icon: MessageSquare, label: 'Messages', path: '/dashboard/messages' },
        { icon: Truck, label: 'Device activation', path: '/dashboard/activation' },
        { icon: Settings, label: 'Devices and settings', path: '/dashboard/settings' },
        { icon: Info, label: 'Information center', path: '/dashboard/info', count: 1 },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                {logo ? (
                    <img src={logo} alt={platformName} className="sidebar-logo" style={{ maxHeight: '40px', maxWidth: '100%' }} />
                ) : (
                    <div className="logo-small">{platformName}</div>
                )}
            </div>

            <div className="user-profile">
                <div className="user-avatar">
                    <UserCircle size={40} />
                </div>
                <div className="user-info">
                    <h3>{user?.first_name} {user?.last_name || 'User'}</h3>
                    <p>ID: {user?.id || '285477'}</p>
                </div>
            </div>

            <nav className="sidebar-nav">
                <div className="nav-group">
                    {menuItems.map((item) => (
                        <NavLink
                            key={item.label}
                            to={item.path}
                            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                        >
                            <item.icon size={18} />
                            <span>{item.label}</span>
                        </NavLink>
                    ))}
                    
                    {/* Lien Superadmin uniquement pour les admins/superusers */}
                    {(user?.is_superuser || user?.user_type === 'admin') && (
                        <NavLink
                            to="/dashboard/admin"
                            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''} admin-nav-item`}
                            style={{ marginTop: '15px', color: '#8b5cf6' }}
                        >
                            <Settings size={18} />
                            <span>Console Superadmin</span>
                        </NavLink>
                    )}
                </div>

                <div className="nav-divider" />

                <div className="nav-group bottom">
                    {bottomItems.map((item) => (
                        <NavLink
                            key={item.label}
                            to={item.path}
                            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                        >
                            <item.icon size={18} />
                            <span>{item.label}</span>
                            {item.count && <span className="item-count">{item.count}</span>}
                        </NavLink>
                    ))}
                </div>
            </nav>

            <button className="logout-btn" onClick={handleLogout}>
                <Power size={18} />
                <span>Logout</span>
            </button>
        </aside>
    );
};

export default Sidebar;
