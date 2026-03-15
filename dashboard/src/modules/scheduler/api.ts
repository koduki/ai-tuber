import { Router } from 'express';
import * as gcp from '../../gcpClient';

const router = Router();

router.get('/', async (req, res) => {
    try {
        const jobs = await gcp.getSchedulerJobs();
        res.json(jobs);
    } catch (err: any) {
        res.status(500).json({ error: err.message });
    }
});

router.post('/:name/run', async (req, res) => {
    try {
        const name = req.params.name;
        await gcp.runSchedulerJob(name);
        res.json({ message: `Job ${name} started` });
    } catch (err: any) {
        res.status(500).json({ error: err.message });
    }
});

export default router;
