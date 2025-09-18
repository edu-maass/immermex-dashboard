import { FC } from 'react';
import { Dashboard } from './components/Dashboard';
import './index.css';

const App: FC = () => {
  return (
    <div className="min-h-screen bg-background">
      <Dashboard />
    </div>
  );
};

export default App;