import { Request, Response } from 'express';
import pool from '../db';

export const getAllGpus = async (req: Request, res: Response) => {
  try {
    const result = await pool.query(`
        SELECT 
            p.productid,
            p.canonicalname,
            p.brand,
            p.model,
            p.vramgb,
            json_agg(
                json_build_object(
                'storename', s.storename,
                'price', l.currentprice,
                'currency', l.currency,
                'link', l.link,
                'imageurl', l.imageurl
                ) ORDER BY l.currentprice ASC
            ) AS listings
        FROM product p
        LEFT JOIN product_listing_match m ON m.productid = p.productid
        LEFT JOIN listing l ON l.listingid = m.listingid
        LEFT JOIN store s ON s.storeid = l.storeid
        GROUP BY p.productid, p.canonicalname, p.brand, p.model, p.vramgb
        ORDER BY p.productid
    `);

    const products = result.rows.map(product => {
        const hasListings = product.listings[0]?.storename !== null;
        return {
            ...product,
            listings: hasListings ? product.listings : [],
            lowestPrice: hasListings ? product.listings[0].price : null
        };
        });

        res.json(products);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to fetch GPUs' });
  }
};

export const getGpuById = async (req: Request, res: Response) => {
  const { id } = req.params;

  try {
    const result = await pool.query(`
        SELECT 
            p.productid,
            p.producttype,
            p.canonicalname,
            p.brand,
            p.series,
            p.manufacturer_normalized,
            p.model_normalized,
            p.coolervariant_normalized,
            p.vramgb,
            p.memorytype,
            p.buswidth,
            p.interfaceversion,
            p.color,
            p.fans,
            p.boostclock,
            p.baseclock,
            json_agg(
                json_build_object(
                'storename', s.storename,
                'price', l.currentprice,
                'currency', l.currency,
                'link', l.link,
                'imageurl', l.imageurl
                ) ORDER BY l.currentprice ASC
            ) AS listings
        FROM product p
        LEFT JOIN product_listing_match m ON m.productid = p.productid
        LEFT JOIN listing l ON l.listingid = m.listingid
        LEFT JOIN store s ON s.storeid = l.storeid
        WHERE p.productid = $1
        GROUP BY p.productid, p.canonicalname, p.brand, p.model, p.vramgb
    `, [id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Product not found' });
    }

    const product = result.rows[0];
    const hasListings = product.listings[0]?.storename !== null;

    res.json({
      ...product,
      listings: hasListings ? product.listings : [],
      lowestPrice: hasListings ? product.listings[0].price : null
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to fetch GPU' });
  }
};