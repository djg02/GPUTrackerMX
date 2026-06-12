import { Router } from 'express';
import { getAllGpus, getGpuById } from '../controllers/gpuController';

const router = Router();

router.get('/', getAllGpus);
router.get('/:id', getGpuById);

export default router;