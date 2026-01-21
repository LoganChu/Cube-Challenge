import React, { useState, useCallback } from 'react';
import { Camera, Upload, X, CheckCircle, AlertCircle } from 'lucide-react';

interface DetectedCard {
  id: string;
  boundingBox: { x: number; y: number; width: number; height: number };
  cropImageUrl: string;
  predictedSet: { id: string; name: string; code: string } | null;
  predictedName: string | null;
  predictedConfidence: number | null;
  confirmed: boolean;
  condition: string;
  quantity: number;
}

interface ScanResult {
  scanId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  scanType: 'single' | 'multi';
  imageUrl: string;
  detectedCards: DetectedCard[];
}

export default function ScanPage() {
  const [scanType, setScanType] = useState<'single' | 'multi'>('single');
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('Image must be less than 10MB');
      return;
    }

    setUploadedImage(file);
    setError(null);
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  }, []);

  const handleUpload = useCallback(async () => {
    if (!uploadedImage) return;

    setIsProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('image', uploadedImage);
      formData.append('scan_type', scanType);

      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/scans/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Upload failed');
      }

      const data = await response.json();
      const scanId = data.data.scan_id;
      setScanResult({
        scanId: scanId,
        status: data.data.status,
        scanType: scanType,
        imageUrl: data.data.image_url,
        detectedCards: []
      });
      
      // Poll for completion
      pollScanStatus(scanId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setIsProcessing(false);
    }
  }, [uploadedImage, scanType]);

  const pollScanStatus = async (scanId: string) => {
    const maxAttempts = 60; // 60 attempts = 30 seconds (500ms interval)
    let attempts = 0;

    const interval = setInterval(async () => {
      try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/scans/${scanId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

        if (!response.ok) {
          throw new Error('Failed to fetch scan status');
        }

        const data = await response.json();
        const result = data.data;

        if (result.status === 'completed') {
          setScanResult({
            scanId: result.scan_id,
            status: result.status,
            scanType: result.scan_type,
            imageUrl: result.image_url,
            detectedCards: (result.detected_cards || []).map((card: any) => ({
              id: card.id,
              boundingBox: card.bounding_box || { x: 0, y: 0, width: 1, height: 1 },
              cropImageUrl: card.crop_image_url || result.image_url,
              predictedSet: { id: '', name: '', code: card.set_code || '' },
              predictedName: card.name || '',
              predictedConfidence: card.confidence || 0,
              confirmed: false,
              condition: '',
              quantity: 1
            }))
          });
          setIsProcessing(false);
          clearInterval(interval);
        } else if (result.status === 'failed') {
          setError('Scan failed');
          setIsProcessing(false);
          clearInterval(interval);
        }

        attempts++;
        if (attempts >= maxAttempts) {
          setError('Scan timeout - please try again');
          setIsProcessing(false);
          clearInterval(interval);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Polling failed');
        setIsProcessing(false);
        clearInterval(interval);
      }
    }, 500);
  };

  const handleCardEdit = async (cardId: string, updates: Partial<DetectedCard>) => {
    // Update local state
    if (!scanResult) return;

    const updatedCards = scanResult.detectedCards.map((card) =>
      card.id === cardId ? { ...card, ...updates, confirmed: true } : card
    );

    setScanResult({ ...scanResult, detectedCards: updatedCards });

    // Card edits are saved locally until final save
    // No need to call API for individual card edits
  };

  const handleSaveToInventory = async () => {
    if (!scanResult) return;

    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const confirmedCards = scanResult.detectedCards.filter((card) => card.confirmed);
      
      if (confirmedCards.length === 0) {
        setError('Please confirm at least one card');
        return;
      }

      const response = await fetch(`${apiUrl}/api/v1/scans/${scanResult.scanId}/save`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          card_ids: confirmedCards.map((card) => card.id),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to save to inventory');
      }

      // Navigate to inventory or show success message
      alert(`Successfully saved ${confirmedCards.length} card(s) to inventory!`);
      window.location.href = '/inventory';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save to inventory');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Scan Cards</h1>

        {/* Scan Type Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Scan Type
          </label>
          <div className="flex gap-4">
            <button
              onClick={() => setScanType('single')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                scanType === 'single'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300'
              }`}
            >
              Single Card
            </button>
            <button
              onClick={() => setScanType('multi')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                scanType === 'multi'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300'
              }`}
            >
              Multiple Cards
            </button>
          </div>
        </div>

        {/* Upload Section */}
        {!scanResult && (
          <div className="bg-white rounded-lg shadow-md p-8 mb-6">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
              {imagePreview ? (
                <div className="space-y-4">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="max-w-full max-h-96 mx-auto rounded-lg"
                  />
                  <button
                    onClick={() => {
                      setImagePreview(null);
                      setUploadedImage(null);
                    }}
                    className="text-red-600 hover:text-red-700 flex items-center justify-center gap-2"
                  >
                    <X className="w-4 h-4" />
                    Remove Image
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <Upload className="w-16 h-16 mx-auto text-gray-400" />
                  <div>
                    <label className="cursor-pointer">
                      <span className="text-blue-600 hover:text-blue-700 font-medium">
                        Click to upload
                      </span>
                      <span className="text-gray-600"> or drag and drop</span>
                      <input
                        type="file"
                        className="hidden"
                        accept="image/*"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleFileSelect(file);
                        }}
                      />
                    </label>
                    <p className="text-sm text-gray-500 mt-2">
                      PNG, JPG, HEIC up to 10MB
                    </p>
                  </div>
                </div>
              )}
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                <AlertCircle className="w-5 h-5" />
                <span>{error}</span>
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={!uploadedImage || isProcessing}
              className="mt-6 w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {isProcessing ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Camera className="w-5 h-5" />
                  Start Scan
                </>
              )}
            </button>
          </div>
        )}

        {/* Scan Results */}
        {scanResult && scanResult.status === 'completed' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Detected Cards ({scanResult.detectedCards.length})
              </h2>

              {scanResult.detectedCards.length === 0 ? (
                <p className="text-gray-600">No cards detected. Please try again.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {scanResult.detectedCards.map((card) => (
                    <CardEditor
                      key={card.id}
                      card={card}
                      onUpdate={(updates) => handleCardEdit(card.id, updates)}
                    />
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-4">
              <button
                onClick={() => {
                  setScanResult(null);
                  setImagePreview(null);
                  setUploadedImage(null);
                  setError(null);
                }}
                className="flex-1 bg-gray-200 text-gray-700 py-3 px-6 rounded-lg font-medium hover:bg-gray-300 transition-colors"
              >
                Scan Another
              </button>
              <button
                onClick={handleSaveToInventory}
                disabled={
                  scanResult.detectedCards.filter((c) => c.confirmed).length === 0
                }
                className="flex-1 bg-green-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                <CheckCircle className="w-5 h-5" />
                Save to Inventory
              </button>
            </div>
          </div>
        )}

        {/* Processing Status */}
        {scanResult && scanResult.status === 'processing' && (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-700">Processing your scan...</p>
            <p className="text-sm text-gray-500 mt-2">
              This may take a few seconds
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

interface CardEditorProps {
  card: DetectedCard;
  onUpdate: (updates: Partial<DetectedCard>) => void;
}

function CardEditor({ card, onUpdate }: CardEditorProps) {
  const [localCard, setLocalCard] = useState(card);

  const handleChange = (field: keyof DetectedCard, value: any) => {
    const updated = { ...localCard, [field]: value, confirmed: true };
    setLocalCard(updated);
    onUpdate({ [field]: value, confirmed: true });
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <img
        src={localCard.cropImageUrl}
        alt="Detected card"
        className="w-full h-48 object-contain bg-gray-50 rounded-lg mb-4"
      />

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Card Name
          </label>
          <input
            type="text"
            value={localCard.predictedName || ''}
            onChange={(e) => handleChange('predictedName', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Card name"
          />
          {localCard.predictedConfidence && (
            <p className="text-xs text-gray-500 mt-1">
              Confidence: {localCard.predictedConfidence.toFixed(1)}%
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Set
          </label>
          <input
            type="text"
            value={localCard.predictedSet?.name || ''}
            onChange={(e) =>
              handleChange('predictedSet', { ...localCard.predictedSet, name: e.target.value })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Set name"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Condition
            </label>
            <select
              value={localCard.condition || ''}
              onChange={(e) => handleChange('condition', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select condition</option>
              <option value="Near Mint">Near Mint</option>
              <option value="Lightly Played">Lightly Played</option>
              <option value="Moderately Played">Moderately Played</option>
              <option value="Heavily Played">Heavily Played</option>
              <option value="Damaged">Damaged</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Quantity
            </label>
            <input
              type="number"
              min="1"
              value={localCard.quantity || 1}
              onChange={(e) => handleChange('quantity', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
