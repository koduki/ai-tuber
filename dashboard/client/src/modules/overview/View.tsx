import React, { useEffect, useState } from 'react';

const Overview: React.FC = () => {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/modules/overview')
            .then(res => res.json())
            .then(json => {
                setData(json);
                setLoading(false);
            })
            .catch(err => {
                console.error('Overview fetch error:', err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div>Loading overview...</div>;
    if (!data) return <div>Error loading data.</div>;

    const cards = [
        { title: 'Scheduler', status: data.schedulerHealth },
        { title: 'Workflow', status: data.workflowState },
        { title: 'Resources', status: data.runningResources },
        { title: 'Public IPs', status: data.externalIps },
        { title: 'Monthly Cost', status: data.billing },
    ];

    return (
        <div className="overview-container">
            <h1>Platform Overview</h1>
            <div className="grid">
                {cards.map(card => (
                    <div key={card.title} className="card">
                        <h3>{card.title}</h3>
                        <div className="value">{card.status.value}</div>
                        <div className="detail">{card.status.detail}</div>
                    </div>
                ))}
            </div>

            <style>{`
                .overview-container { padding: 20px; }
                .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
                .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .card h3 { margin: 0 0 10px 0; color: #666; font-size: 14px; }
                .card .value { font-size: 24px; font-weight: bold; margin-bottom: 5px; }
                .card .detail { font-size: 12px; color: #888; }
            `}</style>
        </div>
    );
};

export default Overview;
