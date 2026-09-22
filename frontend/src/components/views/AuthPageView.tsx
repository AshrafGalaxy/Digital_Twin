import React, { useState } from 'react';
import {
  Activity,
  ArrowRight,
  ShieldCheck,
  Lock,
  Mail,
  User,
  Car,
  Zap,
  FileCheck2,
  AlertCircle,
  CheckCircle2,
  Compass,
  KeyRound,
  Eye,
  EyeOff
} from 'lucide-react';
import { MunicipalRole, AuthUser } from '../../types/twin';
import { loginMunicipalUser, registerMunicipalUser } from '../../services/api';

interface AuthPageViewProps {
  onAuthSuccess: (user: AuthUser) => void;
  onNavigateHome: () => void;
}

export const AuthPageView: React.FC<AuthPageViewProps> = ({ onAuthSuccess, onNavigateHome }) => {
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState<boolean>(false);

  // Sign In State
  const [signInEmail, setSignInEmail] = useState<string>('traffic.engineer@pmc.gov.in');
  const [signInPassword, setSignInPassword] = useState<string>('traffic123');

  // Sign Up State
  const [signUpName, setSignUpName] = useState<string>('');
  const [signUpEmail, setSignUpEmail] = useState<string>('');
  const [signUpPassword, setSignUpPassword] = useState<string>('');
  const [signUpConfirmPassword, setSignUpConfirmPassword] = useState<string>('');
  const [selectedRole, setSelectedRole] = useState<MunicipalRole>('Traffic Systems Engineer');
  const [signUpDepartment, setSignUpDepartment] = useState<string>('');

  const demoAccounts = [
    {
      role: 'Traffic Systems Engineer' as MunicipalRole,
      name: 'Vikram Desai',
      email: 'traffic.engineer@pmc.gov.in',
      password: 'traffic123',
      dept: 'Transportation Operations Division',
      icon: <Car size={16} color="var(--color-primary)" />,
      badge: 'TRAFFIC COMMAND',
      color: '#F59E0B'
    },
    {
      role: 'Energy Grid Manager' as MunicipalRole,
      name: 'Pooja Kulkarni',
      email: 'grid.manager@pmc.gov.in',
      password: 'energy123',
      dept: 'Municipal Utilities & Commercial Grid',
      icon: <Zap size={16} color="var(--color-warning)" />,
      badge: 'GRID UTILITY',
      color: '#10B981'
    },
    {
      role: 'Executive Auditor' as MunicipalRole,
      name: 'Dr. Aris Thorne',
      email: 'auditor@pmc.gov.in',
      password: 'audit123',
      dept: 'Civic Governance & Oversight Council',
      icon: <FileCheck2 size={16} color="var(--color-accent-violet)" />,
      badge: 'ALGORITHMIC GOVERNANCE',
      color: '#38BDF8'
    },
    {
      role: 'Municipal Analyst' as MunicipalRole,
      name: 'Aditi Sharma',
      email: 'analyst@pmc.gov.in',
      password: 'analyst123',
      dept: 'Urban Development & Smart City Mission',
      icon: <Activity size={16} color="var(--color-primary)" />,
      badge: 'CROSS-DOMAIN COMMAND',
      color: '#2F81F7'
    }
  ];

  const handleSelectDemoPersona = (demo: typeof demoAccounts[0]) => {
    setSignInEmail(demo.email);
    setSignInPassword(demo.password);
    setErrorMessage(null);
  };

  const handleSignInSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!signInEmail.trim() || !signInPassword.trim()) {
      setErrorMessage('Please enter both municipal email and password.');
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
      setErrorMessage('Please enter a valid municipal email address.');
      return;
    }

    if (signUpPassword.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.');
      return;
    }

    if (signUpPassword !== signUpConfirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    try {
      const user = await registerMunicipalUser({
        name: signUpName.trim(),
        email: signUpEmail.trim(),
        password: signUpPassword,
        role: selectedRole,
        department: signUpDepartment.trim() || undefined
      });
      onAuthSuccess(user);
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-root">
      {/* Top Floating Mini Header */}
      <header className="auth-top-bar">
        <div className="auth-brand" onClick={onNavigateHome}>
          <Activity size={18} color="var(--color-primary)" style={{ filter: 'drop-shadow(0 0 8px rgba(47, 129, 247, 0.6))' }} />
          <span className="brand-title">Digital Twin</span>
          <span className="brand-corridor">Pune Nagar Road</span>
        </div>
        <button className="auth-back-link" onClick={onNavigateHome}>
          <Compass size={14} />
          <span>Platform Overview</span>
        </button>
      </header>

      {/* Main Authentication Container */}
      <main className="auth-container">
        <div className="auth-card">
          {/* Card Header & Municipal Security Badge */}
          <div className="auth-card-header">
            <div className="auth-security-badge">
              <ShieldCheck size={13} color="var(--color-primary)" />
              <span>Restricted Municipal Access • Nagar Road Corridor</span>
            </div>
            <h1 className="auth-title">
              {authMode === 'signin' ? 'Municipal Gateway Sign In' : 'Register Municipal Officer'}
            </h1>
            <p className="auth-subtitle">
              {authMode === 'signin'
                ? 'Sign in to access real-time arterial kinematics, commercial energy analytics, and calibrated advisories.'
                : 'Register an authorized municipal callsign with designated corridor clearance and operational scope.'}
            </p>

            {/* Mode Switcher Tabs */}
            <div className="auth-mode-tabs">
              <button
                type="button"
                className={`auth-mode-tab ${authMode === 'signin' ? 'active' : ''}`}
                onClick={() => { setAuthMode('signin'); setErrorMessage(null); }}
              >
                Sign In
              </button>
              <button
                type="button"
                className={`auth-mode-tab ${authMode === 'signup' ? 'active' : ''}`}
                onClick={() => { setAuthMode('signup'); setErrorMessage(null); }}
              >
                Create Account
              </button>
            </div>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="auth-error-banner" role="alert">
              <AlertCircle size={15} color="var(--color-danger)" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* TAB 1: SIGN IN */}
          {authMode === 'signin' && (
            <form onSubmit={handleSignInSubmit} className="auth-form">
              {/* Quick Persona Fill */}
              <div className="auth-persona-shortcuts">
                <span className="persona-label">One-Click Evaluator Personas:</span>
                <div className="persona-chips-strip">
                  {demoAccounts.map((demo) => (
                    <button
                      key={demo.role}
                      type="button"
                      className={`persona-chip ${signInEmail === demo.email ? 'active' : ''}`}
                      onClick={() => handleSelectDemoPersona(demo)}
                      title={`Fill ${demo.name} (${demo.role})`}
                    >
                      {demo.icon}
                      <span className="persona-chip-name">{demo.role.split(' ')[0]}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="signin-email">
                  <Mail size={13} />
                  <span>Municipal Email or Callsign</span>
                </label>
                <input
                  id="signin-email"
                  type="text"
                  className="form-input font-mono"
                  placeholder="e.g. traffic.engineer@pmc.gov.in"
                  value={signInEmail}
                  onChange={(e) => setSignInEmail(e.target.value)}
                  autoComplete="username"
                  required
                />
              </div>

              <div className="form-group">
                <div className="form-label-row">
                  <label className="form-label" htmlFor="signin-password">
                    <KeyRound size={13} />
                    <span>Password</span>
                  </label>
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={13} /> : <Eye size={13} />}
                    <span>{showPassword ? 'Hide' : 'Show'}</span>
                  </button>
                </div>
                <input
                  id="signin-password"
                  type={showPassword ? 'text' : 'password'}
                  className="form-input font-mono"
                  placeholder="••••••••"
                  value={signInPassword}
                  onChange={(e) => setSignInPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>

              <div className="auth-remember-row">
                <div className="remember-me-badge">
                  <CheckCircle2 size={13} color="var(--color-success)" />
                  <span>256-bit AES Token Persistence</span>
                </div>
                <span className="demo-hint font-mono">Demo Password: same as role name + 123</span>
              </div>

              <button
                type="submit"
                className="auth-submit-btn"
                disabled={isLoading}
              >
                <span>{isLoading ? 'Authenticating Officer...' : 'Authenticate & Enter Console'}</span>
                <ArrowRight size={15} />
              </button>
            </form>
          )}

          {/* TAB 2: SIGN UP */}
          {authMode === 'signup' && (
            <form onSubmit={handleSignUpSubmit} className="auth-form">
              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="signup-name">
                    <User size={13} />
                    <span>Full Name & Title</span>
                  </label>
                  <input
                    id="signup-name"
                    type="text"
                    className="form-input"
                    placeholder="e.g. Anand Shinde"
                    value={signUpName}
                    onChange={(e) => setSignUpName(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="signup-email">
                    <Mail size={13} />
                    <span>Municipal Email</span>
                  </label>
                  <input
                    id="signup-email"
                    type="email"
                    className="form-input font-mono"
                    placeholder="e.g. anand.shinde@pmc.gov.in"
                    value={signUpEmail}
                    onChange={(e) => setSignUpEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              {/* Municipal Role Selection Cards */}
              <div className="form-group">
                <label className="form-label">
                  <ShieldCheck size={13} />
                  <span>Designate Municipal Authorization Role</span>
                </label>
                <div className="role-selection-grid">
                  {demoAccounts.map((opt) => (
                    <div
                      key={opt.role}
                      className={`role-select-card ${selectedRole === opt.role ? 'selected' : ''}`}
                      onClick={() => {
                        setSelectedRole(opt.role);
                        setSignUpDepartment(opt.dept);
                      }}
                    >
                      <div className="role-card-top">
                        <div className="role-card-icon">{opt.icon}</div>
                        <span className="role-card-badge font-mono">{opt.badge}</span>
                      </div>
                      <span className="role-card-title">{opt.role}</span>
                      <span className="role-card-dept">{opt.dept}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="form-row-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="signup-password">
                    <KeyRound size={13} />
                    <span>Password (min. 6 chars)</span>
                  </label>
                  <input
                    id="signup-password"
                    type="password"
                    className="form-input font-mono"
                    placeholder="••••••••"
                    value={signUpPassword}
                    onChange={(e) => setSignUpPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="signup-confirm-password">
                    <KeyRound size={13} />
                    <span>Confirm Password</span>
                  </label>
                  <input
                    id="signup-confirm-password"
                    type="password"
                    className="form-input font-mono"
                    placeholder="••••••••"
                    value={signUpConfirmPassword}
                    onChange={(e) => setSignUpConfirmPassword(e.target.value)}
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className="auth-submit-btn"
                disabled={isLoading}
              >
                <span>{isLoading ? 'Creating Municipal Account...' : 'Register Officer & Launch Session'}</span>
                <ArrowRight size={15} />
              </button>
            </form>
          )}

          {/* Card Footer Integrity Guarantee */}
          <div className="auth-card-footer">
            <Lock size={12} color="var(--color-text-muted)" />
            <span>Strict read-only decision support • Zero autonomous field actuation authority</span>
          </div>
        </div>
      </main>
    </div>
  );
};
