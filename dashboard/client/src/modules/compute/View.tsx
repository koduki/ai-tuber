import React, { useEffect, useState } from 'react';

interface Instance {
    name: string;
    status: string;
    zone: string;
    internalIp: string;
    externalIp: string;
    description: string;
}

const ComputeView: React.FC = () => {
    const [instances, setInstances] = useState<Instance[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/modules/compute')
            .then(res => res.json())
            .then(data => {
                setInstances(data);
                setLoading(false);
            })
            .catch(err => {
                console.error('Compute fetch error:', err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div>Loading GCE instances...</div>;

    return (
        <div className="module-container">
            <h1>Compute Engine</h1>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Zone</th>
                        <th>External IP</th>
                        <th>Internal IP</th>
                    </tr>
                </thead>
                <tbody>
                    {instances.map(inst => (
                        <tr key={inst.name}>
                            <td>
                                <strong>{inst.name}</strong><br/>
                                <small>{inst.description}</small>
                            </td>
                            <td>
                                <span className={`status-badge ${inst.status === '稼働中' ? 'ok' : 'error'}`}>
                                    {inst.status}
                                </span>
                            </td>
                            <td>{inst.zone}</td>
                            <td>{inst.externalIp}</td>
                            <td>{inst.internalIp}</td>
                        </tr>
                    ))}
                </tbody>
            </table>

            <style>{`
                .module-container { padding: 20px; }
                .data-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
                .data-table th, .data-table td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #edf2f7; }
                .data-table th { background: #f7fafc; font-weight: 600; color: #4a5568; }
                .status-badge { padding: 4px 8px; border-radius: 99px; font-size: 12px; font-weight: 500; }
                .status-badge.ok { background: #c6f6d5; color: #22543d; }
                .status-badge.error { background: #fed7d7; color: #822727; }
                small { color: #888; font-size: 11px; }
            `}</style>
        </div>
    );
};

export default ComputeView;
