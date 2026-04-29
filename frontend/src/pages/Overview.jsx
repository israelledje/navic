import React, { useState, useEffect } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import api from '../api/api';
import './Overview.css';

// Import images
import trackingHeader from '../assets/tracking-header.png';
import missionsHeader from '../assets/missions-header.png';
import fleetHeader from '../assets/fleet-header.png';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
);

const Overview = () => {
    const [stats, setStats] = useState({
        vehicles: { online: 0, pending: 0, offline: 0, other: 0, total: 0 },
        missions: { completed: 0, assigned: 0, failed: 0, other: 0, total: 0 },
        maintenance: { completed: 0, ongoing: 0, expired: 0, other: 0, total: 0 }
    });

    const [mileageData, setMileageData] = useState({
        labels: [],
        datasets: []
    });

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await api.get('/fleet/stats/dashboard_stats/');
                const data = response.data;

                setStats({
                    vehicles: data.vehicles,
                    missions: data.missions,
                    maintenance: data.maintenance
                });

                // ChartJS needs explicit colors if not provided by backend, 
                // but backend provides backgroundColor in datasets now.
                setMileageData(data.mileage);

            } catch (err) {
                console.error("Error fetching dashboard stats:", err);
            }
        };

        fetchStats();

        // Refresh every 30 seconds
        const interval = setInterval(fetchStats, 30000);
        return () => clearInterval(interval);
    }, []);

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    usePointStyle: true,
                    pointStyle: 'circle',
                    padding: 20,
                    font: { size: 11 }
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                stacked: true,
                grid: { color: '#f1f5f9' },
                title: { display: true, text: 'Kilométrage km', font: { size: 12 } }
            },
            x: {
                stacked: true,
                grid: { display: false },
                title: { display: true, text: 'jours', font: { size: 12 }, align: 'end' }
            },
        },
    };

    return (
        <div className="overview-container">
            <header className="page-header">
                <h1>TABLEAU DE BORD</h1>
                <p>Bienvenue dans votre tableau de bord Flow Nav</p>
            </header>

            <div className="stats-grid">
                {/* Suivi Card */}
                <div className="overview-card animated-card">
                    <div className="card-visual">
                        <img src={trackingHeader} alt="Tracking visualization" />
                        <div className="visual-overlay"></div>
                    </div>
                    <div className="card-info-content">
                        <div className="card-main-header">
                            <h3>Suivi</h3>
                            <p>Suivez vos véhicules en temps réel et obtenez l'historique des trajets</p>
                            <a href="#" className="card-action-link">Rapports</a>
                        </div>
                        <div className="card-stats-section">
                            <h4 className="section-title">Véhicules ({stats.vehicles.total})</h4>
                            <ul className="stats-list">
                                <li><span className="dot green"></span> {stats.vehicles.online} En ligne</li>
                                <li><span className="dot green-ring"></span> {stats.vehicles.pending} GPS non mis à jour</li>
                                <li><span className="dot red"></span> {stats.vehicles.offline} Hors-ligne</li>
                                <li><span className="dot gray"></span> {stats.vehicles.other} Autre</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Missions Card */}
                <div className="overview-card animated-card">
                    <div className="card-visual">
                        <img src={missionsHeader} alt="Missions visualization" />
                        <div className="visual-overlay"></div>
                    </div>
                    <div className="card-info-content">
                        <div className="card-main-header">
                            <h3>Missions</h3>
                            <p>Planifier des missions aux employés et contrôler leur mise en œuvre</p>
                            <div className="card-action-links">
                                <a href="#">Ajouter</a>
                                <a href="#">Résumé</a>
                            </div>
                        </div>
                        <div className="card-stats-section">
                            <h4 className="section-title">Missions ({stats.missions.total})</h4>
                            <ul className="stats-list">
                                <li><span className="dot green"></span> {stats.missions.completed} Terminée(s)</li>
                                <li><span className="dot blue"></span> {stats.missions.assigned} Affectée(s)</li>
                                <li><span className="dot red"></span> {stats.missions.failed} En échec</li>
                                <li><span className="dot gray"></span> {stats.missions.other} Autre</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Flotte Card */}
                <div className="overview-card animated-card">
                    <div className="card-visual">
                        <img src={fleetHeader} alt="Fleet visualization" />
                        <div className="visual-overlay"></div>
                    </div>
                    <div className="card-info-content">
                        <div className="card-main-header">
                            <h3>Flotte</h3>
                            <p>Contrôlez l'éco-conduite des véhicules et gérez vos entretiens ainsi que vos dépenses</p>
                            <div className="card-action-links">
                                <a href="#">Flotte</a>
                                <a href="#">Entretien</a>
                                <a href="#">Eco conduite</a>
                            </div>
                        </div>
                        <div className="card-stats-section">
                            <h4 className="section-title">Entretien ({stats.maintenance.total})</h4>
                            <ul className="stats-list">
                                <li><span className="dot green"></span> {stats.maintenance.completed} Terminée(s)</li>
                                <li><span className="dot blue"></span> {stats.maintenance.ongoing} En cours</li>
                                <li><span className="dot red"></span> {stats.maintenance.expired} Expiré</li>
                                <li><span className="dot gray"></span> {stats.maintenance.other} Autre</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            {/* Mileage Chart Section */}
            <div className="chart-card premium-chart">
                <div className="chart-header">
                    <h3>Kilométrage (13/01/2026 - 19/01/2026)</h3>
                </div>
                <div className="chart-content">
                    <Bar data={mileageData} options={chartOptions} />
                </div>
            </div>
        </div>
    );
};

export default Overview;
