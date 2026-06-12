import express from 'express';
import gpuRoutes from './routes/gpu';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use('/api/gpus', gpuRoutes);

app.get('/', (req, res) => {
  res.json({ message: 'GPU Tracker API is running' });
});

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});