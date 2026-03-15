import React, { useEffect, useState } from 'react';

const BillingView: React.FC = () => {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/modules/billing/summary')
            .then(res => res.json())
            .then(data => {
                setData(data);
                setLoading(false);
            })
            .catch(err => {
                console.error('Billing fetch error:', err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div>Loading billing data...</div>;
    if (!data) return <div>No billing data available.</div>;

    return (
        <div className="module-container">
            <h1>Billing Summary</h1>
            <div className="billing-summary">
                <div className="stat-row">
                    <span>Monthly Cost:</span>
                    <strong>{data.monthlyCost}</strong>
                </div>
                <div className="stat-row">
                    <span>Budget:</span>
                    <strong>{data.budget}</strong>
                </div>
                <div className="stat-row">
                    <span>Forecast:</span>
                    <strong>{data.forecast}</strong>
                </div>
            </div>

            <style>{`
                .module-container { padding: 20px; }
                .billing-summary { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); max-width: 400px; }
                .stat-row { display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 18px; }
                .stat-row strong { color: #2d3748; }
            `}</style>
        </div>
    );
};

export default BillingView;
