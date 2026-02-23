import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ArticleList from './components/ArticleList';
import ArticleDetail from './components/ArticleDetail';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <div className="header-content">
            <h1 className="app-title">🔒 Threat Intelligence Aggregator</h1>
            <p className="app-subtitle">AI-Powered Security Feed Analysis</p>
          </div>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<ArticleList />} />
            <Route path="/article/:id" element={<ArticleDetail />} />
          </Routes>
        </main>

        <footer className="app-footer">
          <p>
            Powered by Django + React + Ollama | Data refreshes hourly via Celery
          </p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
