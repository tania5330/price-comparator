import { useState } from 'react';
import { SearchProvider, useSearch } from './context/SearchContext';
import { FavoritesProvider } from './context/FavoritesContext';
import { Sidebar } from './components/Layout/Sidebar';
import { Header } from './components/Layout/Header';
import { Dashboard } from './views/Dashboard';
import { SearchResults } from './views/SearchResults';
import { Favorites } from './views/Favorites';
import { Alerts } from './views/Alerts';

type ViewType = 'dashboard' | 'search' | 'comparison' | 'favorites' | 'alerts' | 'settings';

function AppContent() {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const { performSearch } = useSearch();

  const handleSearch = (payload: { query: string; location: string }) => {
    performSearch(payload.query, payload.location);
    setCurrentView('search');
  };

  const handleViewChange = (view: string) => {
    setCurrentView(view as ViewType);
  };

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'search':
        return (
          <SearchResults />
        );

      case 'favorites':
        return <Favorites />;
      case 'alerts':
        return <Alerts />;
      case 'settings':
        return null; // Settings removed
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar currentView={currentView} onViewChange={handleViewChange} />

      <div className="flex-1 flex flex-col">
        <Header onSearch={handleSearch} onViewChange={handleViewChange} />

        <main className="flex-1 p-6">
          {renderView()}
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <SearchProvider>
      <FavoritesProvider>
        <AppContent />
      </FavoritesProvider>
    </SearchProvider>
  );
}

export default App;
