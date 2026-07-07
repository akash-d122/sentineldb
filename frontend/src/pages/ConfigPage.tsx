import React, { useEffect, useState } from 'react';

interface Threshold {
  id: string;
  instance_id: string;
  metric_name: string;
  warning_threshold: number;
  critical_threshold: number;
}

export default function ConfigPage() {
  const [thresholds, setThresholds] = useState<Threshold[]>([]);
  const [loading, setLoading] = useState(true);

  // Dummy form state
  const [instanceId, setInstanceId] = useState('');
  const [metricName, setMetricName] = useState('');
  const [warnThreshold, setWarnThreshold] = useState('');
  const [critThreshold, setCritThreshold] = useState('');

  const fetchThresholds = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/config/thresholds');
      if (res.ok) {
        setThresholds(await res.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchThresholds();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:8000/api/v1/config/thresholds', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          instance_id: instanceId,
          metric_name: metricName,
          warning_threshold: parseFloat(warnThreshold),
          critical_threshold: parseFloat(critThreshold),
        })
      });
      if (res.ok) {
        fetchThresholds();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/config/thresholds/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchThresholds();
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <div>Loading config...</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Threshold Configuration</h1>

      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Add / Update Threshold</h2>
        <form onSubmit={handleSave} className="flex gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700">Instance ID</label>
            <input type="text" required value={instanceId} onChange={e => setInstanceId(e.target.value)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Metric</label>
            <input type="text" required value={metricName} onChange={e => setMetricName(e.target.value)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Warning</label>
            <input type="number" required value={warnThreshold} onChange={e => setWarnThreshold(e.target.value)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Critical</label>
            <input type="number" required value={critThreshold} onChange={e => setCritThreshold(e.target.value)} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm border p-2" />
          </div>
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700">Save</button>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Instance</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Metric</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Warning</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Critical</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {thresholds.map(t => (
              <tr key={t.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{t.instance_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{t.metric_name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600">{t.warning_threshold}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">{t.critical_threshold}</td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button onClick={() => handleDelete(t.id)} className="text-red-600 hover:text-red-900">Delete</button>
                </td>
              </tr>
            ))}
            {thresholds.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">No thresholds configured.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
