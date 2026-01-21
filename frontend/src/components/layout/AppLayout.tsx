import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  Home, 
  Camera, 
  Grid3x3, 
  ShoppingCart, 
  Bell, 
  Settings,
  User
} from 'lucide-react';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : {};

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'Dashboard' },
    { path: '/scan', icon: Camera, label: 'Scan' },
    { path: '/inventory', icon: Grid3x3, label: 'Inventory' },
    { path: '/marketplace', icon: ShoppingCart, label: 'Marketplace' },
  ];

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const token = localStorage.getItem('access_token') || '';
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await fetch(`${apiUrl}/api/v1/notifications/unread-count`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const json = await res.json();
        if (!cancelled) setUnreadCount(json.data?.count || 0);
      } catch {
        // ignore
      }
    }
    load();
    const id = window.setInterval(load, 10000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [apiUrl, token]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="text-2xl font-bold text-blue-600">
                CardVault
              </Link>
              <div className="hidden md:flex gap-6">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path || (item.path === '/dashboard' && location.pathname === '/');
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg font-medium transition-colors ${
                        isActive
                          ? 'bg-blue-50 text-blue-600'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-700 hidden md:block">{user.username || 'User'}</span>
              <button
                className="relative p-2 text-gray-700 hover:bg-gray-50 rounded-lg"
                onClick={() => navigate('/notifications')}
                aria-label="Notifications"
              >
                <Bell className="w-6 h-6" />
                {unreadCount > 0 && (
                  <span className="absolute top-0 right-0 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {Math.min(unreadCount, 9)}
                  </span>
                )}
              </button>
              <button
                className="p-2 text-gray-700 hover:bg-gray-50 rounded-lg"
                onClick={() => navigate('/settings')}
                aria-label="Settings"
              >
                <Settings className="w-6 h-6" />
              </button>
              <button 
                onClick={handleLogout}
                className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg border border-gray-300"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <div className="flex justify-around items-center h-16">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center justify-center gap-1 px-4 py-2 ${
                  isActive ? 'text-blue-600' : 'text-gray-600'
                }`}
              >
                <Icon className="w-6 h-6" />
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Main Content */}
      <main className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 ${navItems.length > 0 ? 'pb-24 md:pb-8' : ''}`}>
        {children}
      </main>
    </div>
  );
}
