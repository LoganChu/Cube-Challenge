import React, { useEffect, useState } from 'react';
import { Check, Crown, Zap, Star } from 'lucide-react';

type Tier = {
  tier: string;
  name: string;
  max_cards: number;
  max_trend_insights: number;
  price: number;
  price_period: string;
};

type CurrentSubscription = {
  tier: string;
  tier_name: string;
  max_cards: number;
  max_trend_insights: number;
  price: number;
  price_period: string;
};

export default function SubscriptionPage() {
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const token = localStorage.getItem('access_token') || '';

  const [tiers, setTiers] = useState<Tier[]>([]);
  const [currentSub, setCurrentSub] = useState<CurrentSubscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const [tiersRes, subRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/subscription/tiers`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/v1/subscription`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);
      const tiersJson = await tiersRes.json();
      const subJson = await subRes.json();
      setTiers(tiersJson.data || []);
      setCurrentSub(subJson.data);
    } catch (error) {
      console.error('Error fetching subscription data:', error);
    } finally {
      setLoading(false);
    }
  }

  async function upgrade(tier: string) {
    setUpgrading(tier);
    setMessage(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/subscription/upgrade`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tier }),
      });
      const data = await res.json();
      if (res.ok) {
        setMessage(data.data.message || 'Upgrade successful!');
        await fetchData();
      } else {
        setMessage(data.detail || 'Upgrade failed');
      }
    } catch (error) {
      setMessage('Upgrade failed. Please try again.');
    } finally {
      setUpgrading(null);
      setTimeout(() => setMessage(null), 5000);
    }
  }

  function getTierIcon(tier: string) {
    switch (tier) {
      case 'free':
        return <Star className="w-6 h-6" />;
      case 'pro':
        return <Zap className="w-6 h-6" />;
      case 'premium':
        return <Crown className="w-6 h-6" />;
      default:
        return null;
    }
  }

  function getTierColor(tier: string) {
    switch (tier) {
      case 'free':
        return 'border-gray-300';
      case 'pro':
        return 'border-blue-500';
      case 'premium':
        return 'border-purple-500';
      default:
        return 'border-gray-300';
    }
  }

  function getTierBgColor(tier: string) {
    switch (tier) {
      case 'free':
        return 'bg-gray-50';
      case 'pro':
        return 'bg-blue-50';
      case 'premium':
        return 'bg-purple-50';
      default:
        return 'bg-gray-50';
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Subscription Plans</h1>
        <p className="text-gray-600 mt-1">Choose the plan that fits your collection size</p>
      </div>

      {message && (
        <div className={`p-4 rounded-lg ${
          message.includes('Successfully') || message.includes('successful')
            ? 'bg-green-50 text-green-700 border border-green-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {tiers.map((tier) => {
          const isCurrent = currentSub?.tier === tier.tier;
          const isUpgrading = upgrading === tier.tier;
          const canUpgrade = !isCurrent && (tier.tier === 'pro' || tier.tier === 'premium');

          return (
            <div
              key={tier.tier}
              className={`bg-white rounded-lg shadow-md border-2 p-6 ${
                isCurrent ? getTierColor(tier.tier) : 'border-gray-200'
              } ${isCurrent ? getTierBgColor(tier.tier) : ''}`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className={`${
                    tier.tier === 'free' ? 'text-gray-600' :
                    tier.tier === 'pro' ? 'text-blue-600' :
                    'text-purple-600'
                  }`}>
                    {getTierIcon(tier.tier)}
                  </div>
                  <h3 className="text-xl font-bold text-gray-900">{tier.name}</h3>
                </div>
                {isCurrent && (
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-full">
                    Current
                  </span>
                )}
              </div>

              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-gray-900">
                    ${tier.price.toFixed(2)}
                  </span>
                  <span className="text-gray-600">/{tier.price_period}</span>
                </div>
              </div>

              <ul className="space-y-3 mb-6">
                <li className="flex items-start gap-2">
                  <Check className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">
                    <strong>{tier.max_cards.toLocaleString()}</strong> cards max
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">
                    <strong>{tier.max_trend_insights}</strong> trend insights
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Marketplace matching</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">Card scanning</span>
                </li>
              </ul>

              {isCurrent ? (
                <button
                  disabled
                  className="w-full px-4 py-2 bg-gray-200 text-gray-600 rounded-lg font-medium cursor-not-allowed"
                >
                  Current Plan
                </button>
              ) : (
                <button
                  onClick={() => upgrade(tier.tier)}
                  disabled={isUpgrading || !canUpgrade}
                  className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                    canUpgrade
                      ? tier.tier === 'pro'
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-purple-600 text-white hover:bg-purple-700'
                      : 'bg-gray-200 text-gray-600 cursor-not-allowed'
                  }`}
                >
                  {isUpgrading ? 'Upgrading...' : canUpgrade ? 'Upgrade' : 'Current Plan'}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
