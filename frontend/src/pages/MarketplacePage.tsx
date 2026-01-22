import React, { useEffect, useMemo, useState } from 'react';
import { Plus, Trash2, Search, User } from 'lucide-react';

type Want = {
  id: string;
  card_name: string;
  set_code?: string | null;
  min_condition?: string | null;
  max_price?: number | null;
  created_at: string;
};

type Match = {
  want_id: string;
  wanted: { card_name: string; set_code?: string | null };
  owner: { user_id: string; username: string };
  have: {
    inventory_entry_id: string;
    card_name: string;
    set_code: string;
    condition: string;
    quantity: number;
  };
};

export default function MarketplacePage() {
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const token = localStorage.getItem('access_token') || '';

  const [wants, setWants] = useState<Want[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);

  const [cardName, setCardName] = useState('');
  const [setCode, setSetCode] = useState('');

  const placeholderInquiries = useMemo(() => {
    const sampleUsers = ['CardKing', 'HoloHunter', 'TopLoader', 'MintVault', 'SleevedUp'];
    return wants.map((want, index) => ({
      id: want.id,
      card_name: want.card_name,
      set_code: want.set_code,
      suggested_user: sampleUsers[index % sampleUsers.length],
      match_confidence: `${82 + (index % 10)}% match`,
      note: 'Placeholder suggestion based on recent activity',
    }));
  }, [wants]);

  const groupedMatches = useMemo(() => {
    const byWant: Record<string, Match[]> = {};
    for (const m of matches) {
      byWant[m.want_id] = byWant[m.want_id] || [];
      byWant[m.want_id].push(m);
    }
    return byWant;
  }, [matches]);

  async function fetchAll() {
    setLoading(true);
    try {
      const [wRes, mRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/marketplace/wants`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/api/v1/marketplace/matches`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);
      const wJson = await wRes.json();
      const mJson = await mRes.json();
      setWants(wJson.data || []);
      setMatches(mJson.data || []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function addWant(e: React.FormEvent) {
    e.preventDefault();
    if (!cardName.trim()) return;

    await fetch(`${apiUrl}/api/v1/marketplace/wants`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        card_name: cardName.trim(),
        set_code: setCode.trim() ? setCode.trim().toUpperCase() : null,
      }),
    });
    setCardName('');
    setSetCode('');
    await fetchAll();
  }

  async function removeWant(id: string) {
    await fetch(`${apiUrl}/api/v1/marketplace/wants/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    await fetchAll();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Marketplace</h1>
        <p className="text-gray-600 mt-1">
          Add cards you’re looking for. We’ll suggest collectors to contact who have them.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">My Want List</h2>

        <form onSubmit={addWant} className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Card name</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={cardName}
                onChange={(e) => setCardName(e.target.value)}
                placeholder="e.g., Lightning Bolt"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Set code (optional)</label>
            <input
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={setCode}
              onChange={(e) => setSetCode(e.target.value)}
              placeholder="e.g., M21"
            />
          </div>
          <div className="md:col-span-3">
            <button
              type="submit"
              className="w-full md:w-auto bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Add want
            </button>
          </div>
        </form>

        {loading ? (
          <div className="py-10 text-center text-gray-600">Loading…</div>
        ) : wants.length === 0 ? (
          <div className="py-10 text-center text-gray-600">No wants yet. Add one above.</div>
        ) : (
          <div className="mt-6 space-y-3">
            {wants.map((w) => (
              <div key={w.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-gray-900">
                      {w.card_name} {w.set_code ? <span className="text-gray-500">({w.set_code})</span> : null}
                    </p>
                    <p className="text-sm text-gray-600">
                      Matches: {groupedMatches[w.id]?.length || 0}
                    </p>
                  </div>
                  <button
                    onClick={() => removeWant(w.id)}
                    className="text-red-600 hover:text-red-700 flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Remove
                  </button>
                </div>

                <div className="mt-3">
                  {groupedMatches[w.id]?.length ? (
                    <div className="space-y-2">
                      {groupedMatches[w.id].map((m) => (
                        <div key={`${m.want_id}-${m.have.inventory_entry_id}`} className="bg-gray-50 rounded-lg p-3 flex items-center justify-between">
                          <div className="min-w-0">
                            <p className="font-medium text-gray-900 truncate">
                              {m.owner.username} has {m.have.card_name} ({m.have.set_code})
                            </p>
                            <p className="text-sm text-gray-600">
                              {m.have.condition} • Qty {m.have.quantity}
                            </p>
                          </div>
                          <button
                            className="ml-3 px-3 py-2 rounded-lg border border-gray-300 hover:bg-white flex items-center gap-2"
                            onClick={() => {
                              // MVP: no messaging yet—this is the “suggest users to contact” CTA
                              alert(`Contact ${m.owner.username} (coming next): ask about ${m.have.card_name} (${m.have.set_code}).`);
                            }}
                          >
                            <User className="w-4 h-4" />
                            Contact
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-600">No matches yet. </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Marketplace Inquiries</h2>
          <span className="text-xs text-gray-500">Placeholder</span>
        </div>
        {placeholderInquiries.length === 0 ? (
          <div className="text-center py-8 text-gray-600">
            Add a want to see suggested collectors to contact.
          </div>
        ) : (
          <div className="space-y-3">
            {placeholderInquiries.map((inquiry) => (
              <div key={inquiry.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold text-gray-900">
                      {inquiry.card_name}
                      {inquiry.set_code ? <span className="text-gray-500"> ({inquiry.set_code})</span> : null}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">Suggested contact: {inquiry.suggested_user}</p>
                    <p className="text-xs text-gray-500 mt-1">{inquiry.match_confidence} • {inquiry.note}</p>
                  </div>
                  <button
                    className="px-3 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 flex items-center gap-2 text-sm"
                    onClick={() => {
                      alert(`Contact ${inquiry.suggested_user} (placeholder) about ${inquiry.card_name}.`);
                    }}
                  >
                    <User className="w-4 h-4" />
                    Reach out
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

