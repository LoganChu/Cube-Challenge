import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Grid3x3, 
  ShoppingCart, 
  Bell,
  ArrowRight,
  Plus
} from 'lucide-react';

interface DashboardStats {
  total_cards: number;
  total_value: number;
  value_change: number;
  value_change_percent: number;
  recent_scans: number;
  active_listings: number;
  pending_trades: number;
  unread_alerts: number;
}

interface RecentCard {
  id: string;
  card_name: string;
  set_code: string;
  current_value: number;
  value_change: number;
  value_change_percent: number;
}

interface MarketplaceActivity {
  id: string;
  type: 'listing' | 'trade' | 'offer';
  title: string;
  status: string;
  date: string;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trendingCards, setTrendingCards] = useState<RecentCard[]>([]);
  const [marketplaceActivity, setMarketplaceActivity] = useState<MarketplaceActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const placeholderStats: DashboardStats = {
    total_cards: 124,
    total_value: 4823.5,
    value_change: 214.32,
    value_change_percent: 4.6,
    recent_scans: 6,
    active_listings: 8,
    pending_trades: 3,
    unread_alerts: 5
  };

  const placeholderActivity: MarketplaceActivity[] = [
    {
      id: 'placeholder-1',
      type: 'listing',
      title: 'Listed Charizard EX (Secret Rare) for $245',
      status: 'Live • 12 watchers',
      date: '2h ago'
    },
    {
      id: 'placeholder-2',
      type: 'offer',
      title: 'Offer received for Blastoise EX (LP)',
      status: 'Pending response',
      date: 'Yesterday'
    },
    {
      id: 'placeholder-3',
      type: 'trade',
      title: 'Trade chat opened with MintVault',
      status: 'Awaiting confirmation',
      date: '2 days ago'
    }
  ];

  const placeholderTrends = [
    {
      values: [18.2, 18.9, 19.4, 20.1, 19.8, 20.6, 21.4, 22.1],
      label: '7D'
    },
    {
      values: [11.6, 11.4, 11.2, 11.9, 12.4, 12.1, 12.9, 13.3],
      label: '7D'
    }
  ];

  const buildSparklinePoints = (values: number[]) => {
    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min || 1;
    return values
      .map((value, index) => {
        const x = (index / (values.length - 1)) * 100;
        const y = 24 - ((value - min) / range) * 24;
        return `${x},${y}`;
      })
      .join(' ');
  };

  const formatCurrency = (value: number) => `$${value.toFixed(2)}`;

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('access_token');

      // Fetch dashboard stats
      const statsResponse = await fetch(`${apiUrl}/api/v1/dashboard`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData.data);
      }

      // Fetch inventory for trending cards
      const inventoryResponse = await fetch(`${apiUrl}/api/v1/inventory?limit=5&sort_by=value&sort_order=desc`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (inventoryResponse.ok) {
        const inventoryData = await inventoryResponse.json();
        // Mock value changes for demo
        const cards = inventoryData.data.items.map((item: any) => ({
          id: item.id,
          card_name: item.card.name,
          set_code: item.card.set.code,
          current_value: item.current_value?.amount || 0,
          value_change: (item.current_value?.amount || 0) * 0.1, // Mock 10% change
          value_change_percent: 10,
        }));
        setTrendingCards(cards);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const hasRealStats = stats && (stats.total_value > 0 || stats.active_listings > 0 || stats.unread_alerts > 0);
  const displayStats = hasRealStats ? stats : placeholderStats;
  const displayActivity = marketplaceActivity.length ? marketplaceActivity : placeholderActivity;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Overview of your collection and activity</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Cards */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Cards</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {displayStats.total_cards}
              </p>
            </div>
            <div className="bg-blue-100 p-3 rounded-lg">
              <Grid3x3 className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <button
            onClick={() => navigate('/scan')}
            className="mt-4 text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <Plus className="w-4 h-4" />
            Add cards
          </button>
        </div>

        {/* Portfolio Value */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Portfolio Value</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                ${displayStats.total_value.toFixed(2)}
              </p>
              {displayStats.value_change !== 0 && (
                <div className={`flex items-center gap-1 mt-2 text-sm ${
                  displayStats.value_change > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {displayStats.value_change > 0 ? (
                    <TrendingUp className="w-4 h-4" />
                  ) : (
                    <TrendingDown className="w-4 h-4" />
                  )}
                  <span>
                    {displayStats.value_change > 0 ? '+' : ''}
                    {displayStats.value_change_percent.toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
            <div className="bg-green-100 p-3 rounded-lg">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <button
            onClick={() => navigate('/inventory')}
            className="mt-4 text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            View inventory
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Active Listings */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Listings</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {displayStats.active_listings}
              </p>
            </div>
            <div className="bg-purple-100 p-3 rounded-lg">
              <ShoppingCart className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <button
            onClick={() => navigate('/marketplace')}
            className="mt-4 text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            View marketplace
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Alerts */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Unread Alerts</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {displayStats.unread_alerts}
              </p>
            </div>
            <div className="bg-yellow-100 p-3 rounded-lg">
              <Bell className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
          <button
            onClick={() => navigate('/agent')}
            className="mt-4 text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            View alerts
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Trending Cards & Marketplace Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trending Cards */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Trending Cards</h2>
            <button
              onClick={() => navigate('/inventory')}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              View all
            </button>
          </div>
          {trendingCards.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No cards in inventory yet</p>
          ) : (
            <div className="space-y-4">
              {trendingCards.slice(0, 2).map((card, index) => {
                const trend = placeholderTrends[index % placeholderTrends.length];
                const values = trend.values;
                const start = values[0];
                const end = values[values.length - 1];
                const delta = end - start;
                const deltaPercent = (delta / start) * 100;
                return (
                  <div key={card.id} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="min-w-0">
                        <p className="font-medium text-gray-900 truncate">{card.card_name}</p>
                        <p className="text-sm text-gray-600">{card.set_code || 'Unknown set'}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold text-gray-900">{formatCurrency(end)}</p>
                        <div className={`flex items-center gap-1 text-sm ${
                          delta >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {delta >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          <span>{delta >= 0 ? '+' : ''}{deltaPercent.toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>{formatCurrency(start)}</span>
                        <span>{trend.label}</span>
                        <span>{formatCurrency(end)}</span>
                      </div>
                      <svg viewBox="0 0 100 40" className="w-full h-16 mt-2">
                        <defs>
                          <linearGradient id={`trend-${index}`} x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0%" stopColor={delta >= 0 ? '#16A34A' : '#DC2626'} stopOpacity="0.25" />
                            <stop offset="100%" stopColor={delta >= 0 ? '#16A34A' : '#DC2626'} stopOpacity="0" />
                          </linearGradient>
                        </defs>
                        <polyline
                          points={buildSparklinePoints(values)}
                          fill="none"
                          stroke={delta >= 0 ? '#16A34A' : '#DC2626'}
                          strokeWidth="2.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                        <polygon
                          points={`0,40 ${buildSparklinePoints(values)} 100,40`}
                          fill={`url(#trend-${index})`}
                        />
                      </svg>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Marketplace Activity */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Marketplace Activity</h2>
            <button
              onClick={() => navigate('/marketplace')}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              View all
            </button>
          </div>
          {displayActivity.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">No recent marketplace activity</p>
              <button
                onClick={() => navigate('/marketplace')}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Browse marketplace
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {displayActivity.map((activity) => (
                <div key={activity.id} className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium text-gray-900">{activity.title}</p>
                  <p className="text-sm text-gray-600">{activity.type} • {activity.status}</p>
                  <p className="text-xs text-gray-500 mt-1">{activity.date}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>      
    </div>
  );
}
