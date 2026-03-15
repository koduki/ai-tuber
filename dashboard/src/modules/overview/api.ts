import { Router } from 'express';
import * as gcp from '../../gcpClient';

const router = Router();

router.get('/', async (req, res) => {
    try {
        const overview = await gcp.getOverview();
        res.json(overview);
    } catch (err: any) {
        console.error('Overview API error:', err.message);
        res.status(500).json({ error: err.message });
    }
});

export default router;
