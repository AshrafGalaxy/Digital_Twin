import React, { useState, useEffect } from 'react';
import {
  ArrowRight,
  ShieldCheck,
  Mail,
  User,
  KeyRound,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowLeft
} from 'lucide-react';
import { MunicipalRole, AuthUser } from '../../types/twin';
import { loginMunicipalUser, registerMunicipalUser } from '../../services/api';
import { DigitalTwinLogo } from '../common/DigitalTwinLogo';

interface AuthPageViewProps {
  initialMode?: 'signin' | 'signup';
  onAuthSuccess: (user: AuthUser) => void;
  onNavigateHome: () => void;
}

export const AuthPageView: React.FC<AuthPageViewProps> = ({
  initialMode = 'signin',
  onAuthSuccess,
  onNavigateHome
}) => {
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>(initialMode);

  useEffect(() => {
    if (initialMode) {
      setAuthMode(initialMode);
    }
  }, [initialMode]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState<boolean>(false);

  // Sign In State
  const [signInEmail, setSignInEmail] = useState<string>('');
  const [signInPassword, setSignInPassword] = useState<string>('');

  // Sign Up State
  const [signUpName, setSignUpName] = useState<string>('');
  const [signUpEmail, setSignUpEmail] = useState<string>('');
  const [signUpPassword, setSignUpPassword] = useState<string>('');
  const [selectedRole, setSelectedRole] = useState<MunicipalRole>('Traffic Systems Engineer');

  const demoAccounts = [
    {
      role: 'Traffic Systems Engineer' as MunicipalRole,
      label: 'Traffic',
      fullName: 'Traffic Systems Engineer',
      email: 'traffic.engineer@pmc.gov.in',
      password: 'traffic123',
      color: '#F59E0B'
    },
    {
      role: 'Energy Grid Manager' as MunicipalRole,
      label: 'Grid',
      fullName: 'Energy Grid Manager',
      email: 'grid.manager@pmc.gov.in',
      password: 'energy123',
      color: '#10B981'
    },
    {
      role: 'Executive Auditor' as MunicipalRole,
      label: 'Auditor',
      fullName: 'Executive Auditor',
      email: 'auditor@pmc.gov.in',
      password: 'audit123',
      color: '#38BDF8'
    },
    {
      role: 'Municipal Analyst' as MunicipalRole,
      label: 'Analyst',
      fullName: 'Municipal Analyst',
      email: 'analyst@pmc.gov.in',
      password: 'analyst123',
      color: '#2F81F7'
    }
  ];

  const handleQuickSignIn = async (demo: typeof demoAccounts[0]) => {
    setSignInEmail(demo.email);
    setSignInPassword(demo.password);
    setErrorMessage(null);
    setIsLoading(true);
    try {
      const user = await loginMunicipalUser(demo.email, demo.password);
      onAuthSuccess(user);
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignInSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!signInEmail.trim() || !signInPassword.trim()) {
      setErrorMessage('Please enter email and password.');
      return;
    }

    setIsLoading(true);
    try {
      const user = await loginMunicipalUser(signInEmail.trim(), signInPassword.trim());
      onAuthSuccess(user);
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!signUpName.trim()) {
      setErrorMessage('Please enter your full name.');
      return;
    }
    if (!signUpEmail.trim() || !signUpEmail.includes('@')) {
      setErrorMessage('Please enter a valid municipal email.');
      return;
    }
    if (signUpPassword.length < 6) {
      setErrorMessage('Password must be at least 6 characters.');
      return;
    }

    setIsLoading(true);
    try {
      const user = await registerMunicipalUser({
        name: signUpName.trim(),
        email: signUpEmail.trim(),
        password: signUpPassword,
        role: selectedRole
      });
      onAuthSuccess(user);
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-root">
      {/* Sleek Top Navigation */}
      <nav className="auth-top-bar" aria-label="Auth Navigation">
        <button type="button" className="auth-back-link" onClick={onNavigateHome}>
          <ArrowLeft size={14} />
          <span>Back to Overview</span>
        </button>
      </nav>

      {/* Centered Minimalist Card Container */}
      <main className="auth-container">
        <div className="auth-card">
          {/* Centered Brand Header */}
          <div className="auth-header-minimal">
            <div className="auth-logo-badge" onClick={onNavigateHome} title="Go to Platform Overview">
              <DigitalTwinLogo size={32} glow />
            </div>
            <h1 className="auth-title">
              {authMode === 'signin' ? 'Sign in to Twin Console' : 'Create Officer Account'}
            </h1>
            <p className="auth-subtitle">
              {authMode === 'signin'
                ? 'Arterial corridor decision support system'
                : 'Register designated clearance for dual arterial corridor console'}
            </p>
          </div>

          {/* Clean Segmented Mode Switcher */}
          <div className="auth-mode-switch">
            <button
              type="button"
              className={`auth-mode-pill ${authMode === 'signin' ? 'active' : ''}`}
              onClick={() => { setAuthMode('signin'); setErrorMessage(null); }}
            >
              Sign In
            </button>
            <button
              type="button"
              className={`auth-mode-pill ${authMode === 'signup' ? 'active' : ''}`}
              onClick={() => { setAuthMode('signup'); setErrorMessage(null); }}
            >
              Create Account
            </button>
          </div>

          {/* Quick Demo Persona Access */}
          {authMode === 'signin' && (
            <div className="auth-quick-access">
              <span className="quick-access-label">Quick Demo Access</span>
              <div className="quick-access-grid">
                {demoAccounts.map((demo) => (
                  <button
                    key={demo.role}
                    type="button"
                    className="quick-role-btn"
                    onClick={() => handleQuickSignIn(demo)}
                    title={`1-Click Sign In as ${demo.fullName}`}
                    disabled={isLoading}
                  >
                    <span className="quick-role-dot" style={{ backgroundColor: demo.color }} />
                    <span className="quick-role-label">{demo.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {authMode === 'signin' && (
            <div className="auth-divider">
              <span>or sign in with credentials</span>
            </div>
          )}

          {/* Error Banner */}
          {errorMessage && (
            <div className="auth-error-banner" role="alert">
              <AlertCircle size={14} color="#F85149" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Form */}
          {authMode === 'signin' ? (
            <form onSubmit={handleSignInSubmit} className="auth-form-minimal">
              <div className="input-group">
                <label className="input-label" htmlFor="signin-email">
                  Email or callsign
                </label>
                <div className="input-wrapper">
                  <Mail size={14} className="input-icon" />
                  <input
                    id="signin-email"
                    type="text"
                    className="auth-input font-mono"
                    placeholder="officer@pmc.gov.in"
                    value={signInEmail}
                    onChange={(e) => setSignInEmail(e.target.value)}
                    autoComplete="username"
                    required
                  />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label" htmlFor="signin-password">
                  Password
                </label>
                <div className="input-wrapper">
                  <KeyRound size={14} className="input-icon" />
                  <input
                    id="signin-password"
                    type={showPassword ? 'text' : 'password'}
                    className="auth-input font-mono"
                    placeholder="••••••••"
                    value={signInPassword}
                    onChange={(e) => setSignInPassword(e.target.value)}
                    autoComplete="current-password"
                    required
                  />
                  <button
                    type="button"
                    className="input-action-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="auth-btn-primary"
                disabled={isLoading}
              >
                <span>{isLoading ? 'Signing in...' : 'Sign In'}</span>
                <ArrowRight size={14} />
              </button>
            </form>
          ) : (
            <form onSubmit={handleSignUpSubmit} className="auth-form-minimal">
              <div className="input-group">
                <label className="input-label" htmlFor="signup-name">
                  Full Name
                </label>
                <div className="input-wrapper">
                  <User size={14} className="input-icon" />
                  <input
                    id="signup-name"
                    type="text"
                    className="auth-input"
                    placeholder="Officer Name"
                    value={signUpName}
                    onChange={(e) => setSignUpName(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label" htmlFor="signup-email">
                  Municipal Email
                </label>
                <div className="input-wrapper">
                  <Mail size={14} className="input-icon" />
                  <input
                    id="signup-email"
                    type="email"
                    className="auth-input font-mono"
                    placeholder="officer@pmc.gov.in"
                    value={signUpEmail}
                    onChange={(e) => setSignUpEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label" htmlFor="signup-role">
                  Clearance Role
                </label>
                <select
                  id="signup-role"
                  className="auth-select"
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value as MunicipalRole)}
                >
                  <option value="Traffic Systems Engineer">Traffic Systems Engineer (Level 2)</option>
                  <option value="Energy Grid Manager">Energy Grid Manager (Level 2)</option>
                  <option value="Executive Auditor">Executive Auditor (Level 3)</option>
                  <option value="Municipal Analyst">Municipal Analyst (Level 1 Master)</option>
                </select>
              </div>

              <div className="input-group">
                <label className="input-label" htmlFor="signup-password">
                  Password (min 6 characters)
                </label>
                <div className="input-wrapper">
                  <KeyRound size={14} className="input-icon" />
                  <input
                    id="signup-password"
                    type="password"
                    className="auth-input font-mono"
                    placeholder="••••••••"
                    value={signUpPassword}
                    onChange={(e) => setSignUpPassword(e.target.value)}
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className="auth-btn-primary"
                disabled={isLoading}
              >
                <span>{isLoading ? 'Creating account...' : 'Create Account'}</span>
                <ArrowRight size={14} />
              </button>
            </form>
          )}

          {/* Clean Footer Switcher */}
          <div className="auth-footer-toggle">
            {authMode === 'signin' ? (
              <span>
                New officer?{' '}
                <button
                  type="button"
                  className="auth-link-btn"
                  onClick={() => { setAuthMode('signup'); setErrorMessage(null); }}
                >
                  Create an account
                </button>
              </span>
            ) : (
              <span>
                Already have credentials?{' '}
                <button
                  type="button"
                  className="auth-link-btn"
                  onClick={() => { setAuthMode('signin'); setErrorMessage(null); }}
                >
                  Sign in
                </button>
              </span>
            )}
          </div>

          <div className="auth-minimal-disclaimer">
            <ShieldCheck size={12} color="#8B949E" />
            <span>Advisory decision support • Dual arterial corridor console</span>
          </div>
        </div>
      </main>
    </div>
  );
};
