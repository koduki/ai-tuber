import React, { useEffect, useState } from 'react';

interface SchedulerJob {
    name: string;
    displayName: string;
    lastStatus: string;
    lastRunTime: string;
    nextRunTime: string;
    state: string;
    schedule: string;
}

const SchedulerView: React.FC = () => {
    const [jobs, setJobs] = useState<SchedulerJob[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchJobs = () => {
        setLoading(true);
        fetch('/api/modules/scheduler')
            .then(res => res.json())
            .then(data => {
                setJobs(data);
                setLoading(false);
            })
            .catch(err => {
                console.error('Scheduler fetch error:', err);
                setLoading(false);
            });
    };

    useEffect(() => {
        fetchJobs();
    }, []);

    const runJob = (name: string) => {
        fetch(`/api/modules/scheduler/${name}/run`, { method: 'POST' })
            .then(() => alert(`Started job ${name}`))
            .then(() => fetchJobs());
    };

    if (loading) return <div>Loading Scheduler jobs...</div>;

    return (
        <div className="module-container">
            <h1>Cloud Scheduler</h1>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Schedule</th>
                        <th>Last Run</th>
                        <th>Next Run</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {jobs.map(job => (
                        <tr key={job.name}>
                            <td>{job.displayName}</td>
                            <td><code>{job.schedule}</code></td>
                            <td>{job.lastRunTime}</td>
                            <td>{job.nextRunTime}</td>
                            <td>
                                <span className={`status-badge ${job.lastStatus === '成功' ? 'ok' : 'error'}`}>
                                    {job.lastStatus}
                                </span>
                            </td>
                            <td>
                                <button onClick={() => runJob(job.name)}>Run Now</button>
                            </td>
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
                button { background: #3182ce; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; }
                button:hover { background: #2b6cb0; }
            `}</style>
        </div>
    );
};

export default SchedulerView;
