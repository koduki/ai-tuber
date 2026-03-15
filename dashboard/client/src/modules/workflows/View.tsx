import React, { useEffect, useState } from 'react';

interface Workflow {
    name: string;
    location: string;
    revision: string;
    updated: string;
}

interface Execution {
    executionId: string;
    status: string;
    started: string;
    stepName: string;
}

const WorkflowsView: React.FC = () => {
    const [data, setData] = useState<{ workflows: Workflow[], executions: Execution[] } | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/modules/workflows')
            .then(res => res.json())
            .then(json => {
                setData(json);
                setLoading(false);
            })
            .catch(err => {
                console.error('Workflows fetch error:', err);
                setLoading(false);
            });
    }, []);

    if (loading) return <div>Loading Workflows...</div>;
    if (!data) return <div>No data available.</div>;

    return (
        <div className="module-container">
            <h1>Workflows</h1>
            <h3>Active Workflows</h3>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Region</th>
                        <th>Revision</th>
                        <th>Last Updated</th>
                    </tr>
                </thead>
                <tbody>
                    {data.workflows.map(wf => (
                        <tr key={wf.name}>
                            <td>{wf.name}</td>
                            <td>{wf.location}</td>
                            <td>{wf.revision}</td>
                            <td>{wf.updated}</td>
                        </tr>
                    ))}
                </tbody>
            </table>

            <h3>Recent Executions</h3>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Status</th>
                        <th>Step</th>
                        <th>Started</th>
                    </tr>
                </thead>
                <tbody>
                    {data.executions.map(ex => (
                        <tr key={ex.executionId}>
                            <td>{ex.executionId.substring(0, 8)}...</td>
                            <td>
                                <span className={`status-badge ${ex.status === '成功' ? 'ok' : 'error'}`}>
                                    {ex.status}
                                </span>
                            </td>
                            <td>{ex.stepName}</td>
                            <td>{ex.started}</td>
                        </tr>
                    ))}
                </tbody>
            </table>

            <style>{`
                .module-container { padding: 20px; }
                .data-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 30px; }
                .data-table th, .data-table td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #edf2f7; }
                .data-table th { background: #f7fafc; font-weight: 600; color: #4a5568; }
                .status-badge { padding: 4px 8px; border-radius: 99px; font-size: 12px; font-weight: 500; }
                .status-badge.ok { background: #c6f6d5; color: #22543d; }
                .status-badge.error { background: #fed7d7; color: #822727; }
            `}</style>
        </div>
    );
};

export default WorkflowsView;
