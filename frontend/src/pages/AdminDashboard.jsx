import React, { useState, useEffect } from 'react';
import { Users, Truck, Zap, CreditCard, Building2, TrendingUp, MoreHorizontal } from 'lucide-react';
import api from '../api/api';
import './AdminDashboard.css';

const StatCard = ({ title, value, icon: Icon, color, trend }) => (
    <div className="admin-stat-card animate-fade-in">
        <div className="stat-header">
            <span className="stat-title">{title}</span>
            <div className={`stat-icon bg-${color}-light text-${color}`}>
                <Icon size={20} />
            </div>
        </div>
        <div className="stat-value">{value}</div>
        {trend && (
            <div className="stat-trend">
                <TrendingUp size={14} className="text-green" />
                <span className="text-green">{trend}</span> depuis le mois dernier
            </div>
        )}
    </div>
);

const AdminDashboard = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await api.get('/accounts/admin/dashboard/');
                setData(response.data);
            } catch (err) {
                console.error('Failed to load admin stats', err);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    if (loading) return <div className="loading-state">Chargement du dashboard admin...</div>;
    if (!data) return <div className="error-state">Accès non autorisé ou erreur serveur.</div>;

    const { stats, recent_users } = data;

    return (
        <div className="admin-dashboard">
            <div className="page-header">
                <h2>Console Superadmin</h2>
                <p>Vue d'ensemble et gestion globale de la plateforme Navic</p>
            </div>

            <div className="stats-grid">
                <StatCard 
                    title="Utilisateurs Totaux" 
                    value={stats.total_users} 
                    icon={Users} 
                    color="blue" 
                    trend="+12%"
                />
                <StatCard 
                    title="Comptes Entreprises" 
                    value={stats.total_companies} 
                    icon={Building2} 
                    color="purple" 
                />
                <StatCard 
                    title="Balises Déployées" 
                    value={stats.total_devices} 
                    icon={Truck} 
                    color="orange" 
                />
                <StatCard 
                    title="Balises en Ligne" 
                    value={stats.online_devices} 
                    icon={Zap} 
                    color="green" 
                />
                <StatCard 
                    title="Chiffre d'Affaires" 
                    value={`${stats.total_revenue.toLocaleString()} FCFA`} 
                    icon={CreditCard} 
                    color="blue" 
                />
            </div>

            <div className="content-grid">
                <div className="admin-panel users-panel">
                    <div className="panel-header">
                        <h3>Dernières inscriptions</h3>
                        <button className="btn-outline">Voir tous</button>
                    </div>
                    <div className="table-responsive">
                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>Client</th>
                                    <th>Email</th>
                                    <th>Type</th>
                                    <th>Inscription</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recent_users.map(u => (
                                    <tr key={u.id}>
                                        <td>
                                            <div className="client-info">
                                                <div className="avatar">{u.first_name?.[0] || 'U'}</div>
                                                <span>{u.first_name} {u.last_name}</span>
                                            </div>
                                        </td>
                                        <td>{u.email}</td>
                                        <td>
                                            <span className={`badge ${u.user_type}`}>
                                                {u.user_type === 'company' ? 'Entreprise' : 'Particulier'}
                                            </span>
                                        </td>
                                        <td>{new Date(u.created_at).toLocaleDateString()}</td>
                                        <td>
                                            <button className="icon-btn"><MoreHorizontal size={16} /></button>
                                        </td>
                                    </tr>
                                ))}
                                {recent_users.length === 0 && (
                                    <tr>
                                        <td colSpan="5" className="text-center text-muted">Aucun utilisateur récent</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="admin-panel actions-panel">
                    <div className="panel-header">
                        <h3>Actions rapides</h3>
                    </div>
                    <div className="action-buttons">
                        <button className="action-block">
                            <Building2 size={24} className="text-purple" />
                            <span>Créer une Marque Blanche</span>
                        </button>
                        <button className="action-block">
                            <CreditCard size={24} className="text-blue" />
                            <span>Gérer les Forfaits</span>
                        </button>
                        <button className="action-block">
                            <Truck size={24} className="text-orange" />
                            <span>Importer Modèles (CSV)</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
