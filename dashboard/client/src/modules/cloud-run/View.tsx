import React, { useEffect, useState } from 'react';

interface CloudRunService {
    name: string;
    status: string;
    region: string;
    uri: string;
}

const CloudRunView: React.FC = () => {
    const [services, setServices] = useState<CloudRunService[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/modules/cloud-run/services')
            .then(res => res.json())
            .then(data => {
                setServices(data);
                setLoading(false);
            })
            .catch(err => {
                console.error('Cloud Run fetch error:', err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div>Loading Cloud Run services...</div>;

    return (
        <div className="module-container">
            <h1>Cloud Run Services</h1>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Region</th>
                        <th>URL</th>
                    </tr>
                </thead>
                <tbody>
                    {services.map(svc => (
                        <tr key={svc.name}>
                            <td>{svc.name}</td>
                            <td>
                                <span className={`status-badge ${svc.status === '正常' ? 'ok' : 'error'}`}>
                                    {svc.status}
                                </span>
                            </td>
                            <td>{svc.region}</td>
                            <td><a href={svc.uri} target="_blank" rel="noreferrer">Open</a></td>
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
            `}</style>
        </div>
    );
};

export default CloudRunView;
