import express from 'express';
import cors from 'cors';
import gpuRoutes from './routes/gpu';
import { getSitemap } from './controllers/gpuController';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use('/api/gpus', gpuRoutes);
app.get('/api/sitemap.xml', getSitemap)

app.get('/', (req, res) => {
  res.json({ message: 'GPU Tracker API is running' });
});

app.listen(Number(PORT), '0.0.0.0', () => {
  console.log(`Server listening on port ${PORT}`);
});