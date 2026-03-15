import React, { useEffect, useState } from 'react';

interface Build {
    id: string;
    status: string;
    source: string;
    ref: string;
    commit: string;
    triggerName: string;
}

const BuildsView: React.FC = () => {
    const [builds, setBuilds] = useState<Build[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/modules/builds')
            .then(res => res.json())
            .then(data => {
                setBuilds(data);
                setLoading(false);
            })
            .catch(err => {
                console.error('Builds fetch error:', err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div>Loading build history...</div>;

    return (
        <div className="module-container">
            <h1>Cloud Build History</h1>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Build ID</th>
                        <th>Status</th>
                        <th>Source</th>
                        <th>Ref</th>
                        <th>Commit</th>
                    </tr>
                </thead>
                <tbody>
                    {builds.map(build => (
                        <tr key={build.id}>
                            <td><code>{build.id}</code></td>
                            <td>
                                <span className={`status-badge ${build.status === '成功' ? 'ok' : 'error'}`}>
                                    {build.status}
                                </span>
                            </td>
                            <td>{build.source}</td>
                            <td>{build.ref}</td>
                            <td><code>{build.commit}</code></td>
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

export default BuildsView;
