import dotenv from 'dotenv';
import express from 'express';
import bodyParser from 'body-parser';

import routes from './routes';

dotenv.config();

const app = express();

app.use(bodyParser.urlencoded({ extended: false }));
app.use(express.json());

app.get('/healthz', (_req, res) => {
  res.json({ status: 'ok' });
});

app.use(routes);

const port = process.env.PORT ? Number(process.env.PORT) : 3000;

app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
