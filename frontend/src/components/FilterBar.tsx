import { useState } from 'react';
import { FilterParams } from '../types';
import './FilterBar.css';

type Props = {
  onFilterChange: (filters: FilterParams) => void;
  onSearch: (query: string) => void;
};

function FilterBar({ onFilterChange, onSearch }: Props) {
  const [filters, setFilters] = useState({
    source: '',
    threat_type: '',
    severity: '',
    affected_tech: '',
    published_after: '',
    published_before: '',
  });

  const [searchQuery, setSearchQuery] = useState('');

  const handleFilterChange = (field: string, value: string) => {
    const newFilters = { ...filters, [field]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchQuery);
  };

  const handleReset = () => {
    const emptyFilters = {
      source: '',
      threat_type: '',
      severity: '',
      affected_tech: '',
      published_after: '',
      published_before: '',
    };
    setFilters(emptyFilters);
    setSearchQuery('');
    onFilterChange(emptyFilters);
  };

  return (
    <div className="filter-bar">
      <form onSubmit={handleSearchSubmit} className="search-form">
        <input
          type="text"
          placeholder="Search articles..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
        <button type="submit" className="search-btn">Search</button>
      </form>

      <div className="filters">
        <div className="filter-group">
          <label>Source:</label>
          <select
            value={filters.source}
            onChange={(e) => handleFilterChange('source', e.target.value)}
          >
            <option value="">All Sources</option>
            <option value="CISA">CISA</option>
            <option value="Krebs">Krebs on Security</option>
            <option value="BleepingComputer">BleepingComputer</option>
            <option value="US-CERT">US-CERT</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Threat Type:</label>
          <input
            type="text"
            placeholder="e.g., ransomware, phishing"
            value={filters.threat_type}
            onChange={(e) => handleFilterChange('threat_type', e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Severity:</label>
          <select
            value={filters.severity}
            onChange={(e) => handleFilterChange('severity', e.target.value)}
          >
            <option value="">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Affected Tech:</label>
          <input
            type="text"
            placeholder="e.g., Windows, Chrome"
            value={filters.affected_tech}
            onChange={(e) => handleFilterChange('affected_tech', e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Published After:</label>
          <input
            type="date"
            value={filters.published_after}
            onChange={(e) => handleFilterChange('published_after', e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Published Before:</label>
          <input
            type="date"
            value={filters.published_before}
            onChange={(e) => handleFilterChange('published_before', e.target.value)}
          />
        </div>

        <button onClick={handleReset} className="reset-btn">Reset Filters</button>
      </div>
    </div>
  );
}

export default FilterBar;
