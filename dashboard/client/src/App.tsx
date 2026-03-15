import React, { useEffect, useState, Suspense, lazy } from 'react';
import * as Icons from 'lucide-react';
import axios from 'axios';

// Viteの glob import を使用して、各モジュールの View.tsx を自動発見する
const moduleViews = import.meta.glob('./modules/*/View.tsx');

interface ModuleMetadata {
  id: string;
  title: string;
  icon: string;
}

const App: React.FC = () => {
  const [manifest, setManifest] = useState<ModuleMetadata[]>([]);
  const [activeModuleId, setActiveModuleId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // モジュール一覧を取得
    axios.get('/api/manifest')
      .then(res => {
        setManifest(res.data);
        if (res.data.length > 0) {
          setActiveModuleId(res.data[0].id);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch manifest:', err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="loading">Initializing Dashboard...</div>;

  // 動的コンポーネントのロード
  const renderActiveModule = () => {
    if (!activeModuleId) return <div>No module selected.</div>;
    
    const viewPath = `../../src/modules/${activeModuleId}/View.tsx`;
    if (!moduleViews[viewPath]) {
      return <div>View not found for module {activeModuleId}</div>;
    }

    const ModuleView = lazy(moduleViews[viewPath] as any);
    
    return (
      <Suspense fallback={<div>Loading module view...</div>}>
        <ModuleView />
      </Suspense>
    );
  };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="logo">AI Tuber IDP</div>
        <nav>
          {manifest.map(mod => {
            const IconComponent = (Icons as any)[mod.icon] || Icons.HelpCircle;
            return (
              <button
                key={mod.id}
                className={activeModuleId === mod.id ? 'active' : ''}
                onClick={() => setActiveModuleId(mod.id)}
              >
                <IconComponent size={20} />
                <span>{mod.title}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      
      <main className="content">
        <header className="top-bar">
          <div className="current-tab">
            {manifest.find(m => m.id === activeModuleId)?.title || 'Settings'}
          </div>
          <div className="user-info">
            <button onClick={() => window.location.href = '/auth/logout'}>Logout</button>
          </div>
        </header>
        <div className="module-content">
          {renderActiveModule()}
        </div>
      </main>

      <style>{`
        body, html, #root { margin: 0; padding: 0; height: 100%; font-family: 'Inter', sans-serif; background: #f4f7f9; }
        .app-layout { display: flex; height: 100vh; }
        .sidebar { width: 240px; background: #1a202c; color: white; display: flex; flex-direction: column; }
        .sidebar .logo { padding: 20px; font-weight: bold; font-size: 18px; border-bottom: 1px solid #2d3748; }
        .sidebar nav { flex: 1; padding: 10px; }
        .sidebar button { 
          display: flex; align-items: center; width: 100%; padding: 12px; margin-bottom: 5px;
          background: transparent; border: none; color: #a0aec0; cursor: pointer; border-radius: 6px;
          transition: all 0.2s; gap: 12px;
        }
        .sidebar button:hover { background: #2d3748; color: white; }
        .sidebar button.active { background: #3182ce; color: white; }
        
        .content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .top-bar { 
          height: 60px; background: white; border-bottom: 1px solid #e2e8f0; 
          display: flex; align-items: center; justify-content: space-between; padding: 0 20px;
        }
        .current-tab { font-weight: 600; color: #2d3748; }
        .module-content { flex: 1; overflow-y: auto; }
        .loading { display: flex; height: 100vh; align-items: center; justify-content: center; font-size: 20px; }
      `}</style>
    </div>
  );
};

export default App;
