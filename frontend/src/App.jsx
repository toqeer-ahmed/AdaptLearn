import { useState } from 'react';
import './App.css';

function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const checkBackendHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/health');
      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }
      const data = await response.json();
      setHealthStatus(data);
    } catch (err) {
      setError(err.message || 'Failed to reach backend server');
      setHealthStatus(null);
    } finally {
      setLoading(false);
    }
  };

  const modules = [
    {
      code: 'M1',
      title: 'User & Course Management',
      owner: 'Hiba',
      description: 'Handles user registration, authentication, role access (student, instructor, admin), and course catalog creation.',
    },
    {
      code: 'M2',
      title: 'Quiz & Assessment Engine',
      owner: 'Mustajaab',
      description: 'Manages dynamic assessments, question banks, answer evaluations, scoring rules, and automated grading.',
    },
    {
      code: 'M3',
      title: 'Adaptive Learning Engine',
      owner: 'Toqeer',
      description: 'Applies adaptive decision models to adjust question difficulty and tailor concept remediation based on performance.',
    },
    {
      code: 'M4',
      title: 'Personalized Learning Paths',
      owner: 'Hiba',
      description: 'Constructs custom learning trajectories, sequencing lessons and milestones to guide student progression.',
    },
    {
      code: 'M5',
      title: 'Progress Analytics & Dashboard',
      owner: 'Toqeer',
      description: 'Provides visual insights, mastery metrics, student progress tracking, and performance reporting.',
    },
  ];

  return (
    <div className="container">
      {/* Header */}
      <header className="header">
        <div className="logo-section">
          <div className="logo-icon">AL</div>
          <div>
            <h1 className="logo-title">AdaptLearn</h1>
            <p className="logo-subtitle">Adaptive Education Platform</p>
          </div>
        </div>
        <div className="badge">Sprint 0: Project Initialized</div>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <h2 className="hero-title">Welcome to AdaptLearn</h2>
        <p className="hero-description">
          A personalized education environment bridging intelligent assessments, adaptive learning pathways,
          and continuous progress analytics.
        </p>

        {/* Backend Connectivity Check Card */}
        <div className="health-card">
          <div className="health-header">
            <h3>Backend Connectivity Status</h3>
            <button
              onClick={checkBackendHealth}
              disabled={loading}
              className="health-button"
            >
              {loading ? 'Checking...' : 'Check /health Endpoint'}
            </button>
          </div>

          {healthStatus && (
            <div className="status-box success">
              <span className="indicator active"></span>
              <div>
                <strong>Connected to Backend:</strong>
                <pre>{JSON.stringify(healthStatus, null, 2)}</pre>
              </div>
            </div>
          )}

          {error && (
            <div className="status-box error">
              <span className="indicator offline"></span>
              <div>
                <strong>Connection Error:</strong> {error}
                <p className="hint">Make sure FastAPI is running on <code>http://localhost:8000</code>.</p>
              </div>
            </div>
          )}

          {!healthStatus && !error && (
            <p className="health-prompt">
              Click the button above to test communication with the FastAPI backend health endpoint.
            </p>
          )}
        </div>
      </section>

      {/* Modules Grid */}
      <section className="modules-section">
        <h3 className="section-title">Team Modules & Responsibilities</h3>
        <div className="module-grid">
          {modules.map((mod) => (
            <div key={mod.code} className="module-card">
              <div className="module-card-header">
                <span className="module-code">{mod.code}</span>
                <span className="module-owner">Lead: {mod.owner}</span>
              </div>
              <h4 className="module-title">{mod.title}</h4>
              <p className="module-desc">{mod.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Tech Stack Summary */}
      <section className="stack-section">
        <h3 className="section-title">Planned Technology Stack</h3>
        <div className="stack-badges">
          <span className="stack-badge">Frontend: React (Vite)</span>
          <span className="stack-badge">Backend: FastAPI (Python 3.10+)</span>
          <span className="stack-badge">Database: PostgreSQL (Planned)</span>
          <span className="stack-badge">API: RESTful / JSON</span>
          <span className="stack-badge">Testing: Pytest & React Testing</span>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>AdaptLearn &bull; Software Quality Assurance (SE431) University Project</p>
        <p className="footer-sub">Team: Hiba, Mustajaab, Toqeer</p>
      </footer>
    </div>
  );
}

export default App;
