import { Router } from 'express';
import { getAllGpus, getGpuById, getGpuFilters } from '../controllers/gpuController';

const router = Router();

router.get('/', getAllGpus);
router.get('/filters', getGpuFilters);
router.get('/:id', getGpuById);

export default router;