import { FC } from 'react';
import { Dashboard } from './components/Dashboard';
import './index.css';

const App: FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-secondary/60 to-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Dashboard />
      </div>
    </div>
  );
};

export default App;