import React, { useEffect, useState } from 'react';
import { Save, MapPin } from 'lucide-react';

type Settings = {
  inventory_public: boolean;
  marketplace_enabled: boolean;
  notification_in_app: boolean;
  city?: string | null;
  state_province?: string | null;
  country?: string | null;
};

export default function SettingsPage() {
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const token = localStorage.getItem('access_token') || '';

  const [settings, setSettings] = useState<Settings | null>(null);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const res = await fetch(`${apiUrl}/api/v1/settings`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      setSettings(json.data);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function save() {
    if (!settings) return;
    setSaving(true);
    setStatus(null);
    try {
      await fetch(`${apiUrl}/api/v1/settings`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });
      setStatus('Saved');
    } catch {
      setStatus('Save failed');
    } finally {
      setSaving(false);
      setTimeout(() => setStatus(null), 2000);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Privacy, marketplace, and notifications.</p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
        {!settings ? (
          <div className="py-8 text-center text-gray-600">Loading…</div>
        ) : (
          <>
            <ToggleRow
              title="Enable marketplace matching"
              description="Allow other users to discover you as a match when they want cards you have."
              value={settings.marketplace_enabled}
              onChange={(v) => setSettings({ ...settings, marketplace_enabled: v })}
            />
            <ToggleRow
              title="Make inventory discoverable for matching"
              description="If enabled, your inventory can be used to generate matches (no prices or full vault exposed)."
              value={settings.inventory_public}
              onChange={(v) => setSettings({ ...settings, inventory_public: v })}
            />
            <ToggleRow
              title="In-app notifications"
              description="Show match + trend notifications in the bell."
              value={settings.notification_in_app}
              onChange={(v) => setSettings({ ...settings, notification_in_app: v })}
            />

            <div className="border-t border-gray-200 pt-4 mt-4">
              <div className="flex items-center gap-2 mb-4">
                <MapPin className="w-5 h-5 text-gray-600" />
                <h3 className="text-lg font-semibold text-gray-900">Location</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Optional: Share your location to help find local trading partners and meetups.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    value={settings.city || ''}
                    onChange={(e) => setSettings({ ...settings, city: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., New York"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    State/Province
                  </label>
                  <input
                    type="text"
                    value={settings.state_province || ''}
                    onChange={(e) => setSettings({ ...settings, state_province: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., NY or Ontario"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Country
                  </label>
                  <input
                    type="text"
                    value={settings.country || ''}
                    onChange={(e) => setSettings({ ...settings, country: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., USA or Canada"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={save}
                disabled={saving}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Saving…' : 'Save'}
              </button>
              {status && <span className="text-sm text-gray-600">{status}</span>}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ToggleRow({
  title,
  description,
  value,
  onChange,
}: {
  title: string;
  description: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-gray-100 pb-4">
      <div>
        <p className="font-semibold text-gray-900">{title}</p>
        <p className="text-sm text-gray-600 mt-1">{description}</p>
      </div>
      <button
        onClick={() => onChange(!value)}
        className={`w-12 h-7 rounded-full relative transition-colors ${value ? 'bg-blue-600' : 'bg-gray-300'}`}
        aria-label={title}
      >
        <span
          className={`absolute top-0.5 w-6 h-6 rounded-full bg-white transition-transform ${value ? 'translate-x-5' : 'translate-x-0.5'}`}
        />
      </button>
    </div>
  );
}

