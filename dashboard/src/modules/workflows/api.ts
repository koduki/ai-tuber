import { Router } from 'express';
import * as gcp from '../../gcpClient';

const router = Router();

router.get('/', async (req, res) => {
    try {
        const [workflows, executions] = await Promise.all([
            gcp.getWorkflowInfo(),
            gcp.getWorkflowExecutions(),
        ]);
        res.json({ workflows, executions });
    } catch (err: any) {
        res.status(500).json({ error: err.message });
    }
});

export default router;
