import React, { useState, useEffect } from 'react';
import { Search, Filter, Grid, List, ChevronDown } from 'lucide-react';

interface InventoryEntry {
  id: string;
  card: {
    id: string;
    name: string;
    set: { id: string; name: string; code: string };
    image_url: string;
  };
  quantity: number;
  condition: string;
  current_value: {
    amount: number;
    currency: string;
    confidence: string;
  } | null;
  scanned_at: string;
}

export default function InventoryPage() {
  const [entries, setEntries] = useState<InventoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    set_id: '',
    condition: '',
    sort_by: 'date_added',
    sort_order: 'desc' as 'asc' | 'desc',
  });

  useEffect(() => {
    fetchInventory();
  }, [filters, searchQuery]);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        search: searchQuery,
        sort_by: filters.sort_by,
        sort_order: filters.sort_order,
        ...(filters.set_id && { set_id: filters.set_id }),
        ...(filters.condition && { condition: filters.condition }),
      });

      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/inventory?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch inventory');

      const data = await response.json();
      setEntries(data.data.items || []);
    } catch (error) {
      console.error('Error fetching inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  const totalValue = entries.reduce((sum, entry) => {
    return sum + (entry.current_value?.amount || 0) * entry.quantity;
  }, 0);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My Inventory</h1>
          <p className="text-gray-600">
            {entries.length} cards • Total Value: ${totalValue.toFixed(2)}
          </p>
        </div>

        {/* Search & Filters */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by card name or set..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="flex gap-2">
              <select
                value={filters.condition}
                onChange={(e) => setFilters({ ...filters, condition: e.target.value })}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Conditions</option>
                <option value="Near Mint">Near Mint</option>
                <option value="Lightly Played">Lightly Played</option>
                <option value="Moderately Played">Moderately Played</option>
                <option value="Heavily Played">Heavily Played</option>
                <option value="Damaged">Damaged</option>
              </select>

              <select
                value={filters.sort_by}
                onChange={(e) => setFilters({ ...filters, sort_by: e.target.value })}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="date_added">Date Added</option>
                <option value="name">Name</option>
                <option value="value">Value</option>
                <option value="condition">Condition</option>
              </select>

              <button
                onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                {viewMode === 'grid' ? <List className="w-5 h-5" /> : <Grid className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Inventory Content */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="mt-4 text-gray-600">Loading inventory...</p>
          </div>
        ) : entries.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <p className="text-gray-600 mb-4">No cards in your inventory yet.</p>
            <a href="/scan" className="text-blue-600 hover:text-blue-700 font-medium">
              Start scanning cards →
            </a>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {entries.map((entry) => (
              <CardGridItem key={entry.id} entry={entry} />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Card
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Set
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Condition
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Value
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {entries.map((entry) => (
                  <tr key={entry.id} className="hover:bg-gray-50 cursor-pointer">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <img
                          src={entry.card.image_url}
                          alt={entry.card.name}
                          className="w-12 h-16 object-contain mr-3"
                        />
                        <span className="font-medium text-gray-900">{entry.card.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {entry.card.set.code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {entry.condition}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {entry.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {entry.current_value
                        ? `$${(entry.current_value.amount * entry.quantity).toFixed(2)}`
                        : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function CardGridItem({ entry }: { entry: InventoryEntry }) {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow cursor-pointer">
      <img
        src={entry.card.image_url}
        alt={entry.card.name}
        className="w-full h-48 object-contain bg-gray-50"
      />
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 mb-1 truncate">{entry.card.name}</h3>
        <p className="text-sm text-gray-600 mb-2">{entry.card.set.code}</p>
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600">{entry.condition}</span>
          <span className="font-medium text-gray-900">
            {entry.current_value
              ? `$${(entry.current_value.amount * entry.quantity).toFixed(2)}`
              : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
}
