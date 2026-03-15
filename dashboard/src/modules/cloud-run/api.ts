import { Router } from 'express';
import * as gcp from '../../gcpClient';

const router = Router();

router.get('/services', async (req, res) => {
    try {
        const services = await gcp.getCloudRunServices();
        res.json(services);
    } catch (err: any) {
        res.status(500).json({ error: err.message });
    }
});

router.get('/jobs', async (req, res) => {
    try {
        const jobs = await gcp.getCloudRunJobs();
        res.json(jobs);
    } catch (err: any) {
        res.status(500).json({ error: err.message });
    }
});

export default router;
