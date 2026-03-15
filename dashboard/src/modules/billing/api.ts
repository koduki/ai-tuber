import { Router } from 'express';
import * as gcp from '../../gcpClient';

const router = Router();

router.get('/summary', async (req, res) => {
    try {
        const billing = await gcp.getBillingSummary();
        res.json(billing);
    } catch (err: any) {
        res.status(500).json({ error: err.message });
    }
});

export default router;
