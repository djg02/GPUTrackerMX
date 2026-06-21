import { Router } from 'express';
import { getAllGpus, getGpuById, getGpuFilters, getGpuHistory } from '../controllers/gpuController';

const router = Router();

router.get('/', getAllGpus);
router.get('/filters', getGpuFilters);
router.get('/:id', getGpuById);
router.get('/:id/history', getGpuHistory);

export default router;