import { Router } from 'express';
import * as gcp from '../../gcpClient';

const router = Router();

router.get('/', async (req, res) => {
    try {
        const instances = await gcp.getComputeInstances();
        res.json(instances);
    } catch (err: any) {
        res.status(500).json({ error: err.message });
    }
});

export default router;
