import React, { useEffect, useState } from 'react';
import { Check, Bell } from 'lucide-react';

type Notification = {
  id: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
};

export default function NotificationsPage() {
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const token = localStorage.getItem('access_token') || '';
  const [items, setItems] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const placeholderNotifications: Notification[] = [
    {
      id: 'placeholder-1',
      type: 'trend',
      title: 'Portfolio spike detected',
      message: 'Charizard EX jumped 12.4% in the last 24 hours.',
      read: false,
      created_at: new Date(Date.now() - 1000 * 60 * 45).toISOString()
    },
    {
      id: 'placeholder-2',
      type: 'price_up',
      title: 'Price rising reminder',
      message: 'Blastoise EX is up 6.2% this week. Consider listing or trading.',
      read: false,
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString()
    },
    {
      id: 'placeholder-3',
      type: 'price_down',
      title: 'Price dip alert',
      message: 'Venusaur EX fell 4.7% since yesterday. Watch for buying opportunities.',
      read: false,
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 8).toISOString()
    },
    {
      id: 'placeholder-4',
      type: 'match',
      title: 'New marketplace match',
      message: 'MintVault has a card on your want list: Blastoise EX (LP).',
      read: false,
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString()
    },
    {
      id: 'placeholder-5',
      type: 'listing',
      title: 'Listing watch update',
      message: 'Your Venusaur EX listing picked up 3 new watchers.',
      read: true,
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString()
    }
  ];

  async function fetchNotifications() {
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/notifications`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      setItems(json.data || []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchNotifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function markRead(id: string) {
    await fetch(`${apiUrl}/api/v1/notifications/${id}/read`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Notifications</h1>
        <p className="text-gray-600 mt-1">
          Marketplace matches and portfolio trends.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        {loading ? (
          <div className="py-10 text-center text-gray-600">Loading…</div>
        ) : items.length === 0 ? (
          <div className="py-10 text-center text-gray-600">
            <Bell className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            No notifications yet.
          </div>
        ) : (
          <div className="space-y-3">
            {(items.length ? items : placeholderNotifications).map((n) => (
              <div key={n.id} className={`border rounded-lg p-4 ${n.read ? 'border-gray-200 bg-white' : 'border-blue-200 bg-blue-50'}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-semibold text-gray-900">{n.title}</p>
                    <p className="text-sm text-gray-700 mt-1">{n.message}</p>
                    <p className="text-xs text-gray-500 mt-2">{new Date(n.created_at).toLocaleString()}</p>
                  </div>
                  {!n.read && (
                    <button
                      onClick={() => markRead(n.id)}
                      className="px-3 py-2 rounded-lg border border-gray-300 hover:bg-white flex items-center gap-2"
                    >
                      <Check className="w-4 h-4" />
                      Mark read
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

