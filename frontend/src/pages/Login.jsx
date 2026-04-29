import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, Eye, EyeOff, Globe, Apple, Smartphone } from 'lucide-react';
import api from '../api/api';
import './Login.css';
import { ThemeContext } from '../App';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { platformName, logo } = useContext(ThemeContext);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await api.post('/accounts/auth/login/', { email, password });
            localStorage.setItem('access_token', response.data.access);
            localStorage.setItem('refresh_token', response.data.refresh);
            navigate('/dashboard');
        } catch (err) {
            setError('Identifiants invalides ou erreur serveur.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-left">
                <div className="login-content">
                    <div className="logo-section">
                        {logo ? (
                            <img src={logo} alt={platformName} className="login-logo-img" style={{ maxHeight: '60px', maxWidth: '100%' }} />
                        ) : (
                            <h1 className="logo-text">{platformName}</h1>
                        )}
                    </div>

                    <form onSubmit={handleSubmit} className="login-form">
                        <div className="input-group">
                            <div className="input-icon">
                                <User size={20} />
                            </div>
                            <input
                                type="email"
                                placeholder="Email address"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>

                        <div className="input-group">
                            <div className="input-icon">
                                <Lock size={20} />
                            </div>
                            <input
                                type={showPassword ? "text" : "password"}
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                            <div className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </div>
                        </div>

                        <div className="forgot-password">
                            <a href="#">Forgot password?</a>
                        </div>

                        {error && <div className="error-message">{error}</div>}

                        <button type="submit" className="login-btn" disabled={loading}>
                            {loading ? 'LOGGING IN...' : 'LOGIN'}
                        </button>

                        <div className="registration-link">
                            <a href="#">Registration</a>
                        </div>

                        <div className="app-icons">
                            <Apple size={20} />
                            <Smartphone size={20} />
                        </div>
                    </form>

                    <div className="login-footer">
                        <p className="footer-title">{platformName} Tracking Platform</p>
                        <div className="footer-links">
                            <div className="lang-selector">
                                <Globe size={16} />
                                <span>English</span>
                            </div>
                            <a href="#">About Us</a>
                        </div>
                    </div>
                </div>
            </div>
            <div className="login-right">
                {/* The background image is handled via CSS */}
            </div>
        </div>
    );
};

export default Login;
