import { Request, Response } from 'express';
import pool from '../db';

export const getAllGpus = async (req: Request, res: Response) => {
 const { brand, minVram, maxPrice, minPrice, page = '1', limit = '20', sort, manufacturer, color, inStock} = req.query;
    const pageNum = Number(page);
    const limitNum = Number(limit);
    const offset = (pageNum - 1) * limitNum;

    const sortOptions: Record<string, string> = {
      price_asc: 'MIN(l.currentprice) ASC',
      price_desc: 'MIN(l.currentprice) DESC',
      name_asc: 'p.canonicalname ASC',
      name_desc: 'p.canonicalname DESC',
    };
    const orderByClause = sortOptions[sort as string] || 'p.productid ASC';

  try {
    const conditions: string[] = [];
    const havingConditions: string[] = [];
    const values: any[] = [];

    if (brand) {
      values.push(brand);
      conditions.push(`p.brand = $${values.length}`);
    }

    if (minVram) {
      values.push(Number(minVram));
      conditions.push(`p.vramgb >= $${values.length}`);
    }

    if (maxPrice) {
      values.push(Number(maxPrice));
      havingConditions.push(`MIN(l.currentprice) <= $${values.length}`);
    }

    if (minPrice) {
      values.push(Number(minPrice));
      havingConditions.push(`MIN(l.currentprice) >= $${values.length}`);
    }

    if (manufacturer) {
      values.push(manufacturer);
      conditions.push(`p.manufacturer_normalized = $${values.length}`);
    }

    if (color) {
      values.push(color);
      conditions.push(`p.color = $${values.length}`);
    }

    if (inStock === 'true') {
      havingConditions.push(`COUNT(*) FILTER (WHERE l.availabilitystatus IN ('InStock', 'Available')) > 0`);
    }

    const whereClause = conditions.length > 0 
      ? `WHERE ${conditions.join(' AND ')}` 
      : '';
    
    const havingClause = havingConditions.length > 0
      ? `HAVING ${havingConditions.join(' AND ')}`
      : '';

    const countResult = await pool.query(`
            SELECT COUNT(*) FROM (
              SELECT p.productid
              FROM product p
              LEFT JOIN product_listing_match m ON m.productid = p.productid
              LEFT JOIN listing l ON l.listingid = m.listingid
              LEFT JOIN store s ON s.storeid = l.storeid
              ${whereClause}
              GROUP BY p.productid
              ${havingClause}
            ) AS filtered
        `, values);

        const totalCount = Number(countResult.rows[0].count);

    values.push(limitNum, offset);
    const result = await pool.query(`
        SELECT 
            p.productid,
            p.canonicalname,
            p.brand,
            p.manufacturer_normalized,
            p.model_normalized,
            p.coolervariant_normalized,
            p.vramgb,
            json_agg(
                json_build_object(
                'storename', s.storename,
                'price', l.currentprice,
                'currency', l.currency,
                'link', l.link,
                'imageurl', l.imageurl,
                'availabilitystatus', l.availabilitystatus
                ) ORDER BY l.currentprice ASC
            ) AS listings
        FROM product p
        LEFT JOIN product_listing_match m ON m.productid = p.productid
        LEFT JOIN listing l ON l.listingid = m.listingid
        LEFT JOIN store s ON s.storeid = l.storeid
        ${whereClause}
        GROUP BY p.productid, p.canonicalname, p.brand, p.model, p.vramgb
        ${havingClause}
        ORDER BY ${orderByClause}
        LIMIT $${values.length - 1} OFFSET $${values.length}
    `, values);

    const products = result.rows.map(product => {
        const hasListings = product.listings[0]?.storename !== null;

        let lowestPrice = null;
        if (hasListings) {
          const inStockListings = product.listings.filter(
            (l: any) => l.availabilitystatus === 'InStock' || l.availabilitystatus === 'Available'
          );
          const source = inStockListings.length > 0 ? inStockListings : product.listings;
          lowestPrice = source[0].price; // already sorted by price ASC from SQL
        }

        return {
            ...product,
            listings: hasListings ? product.listings : [],
            lowestPrice
        };
        });

    res.json({
      page: pageNum,
      limit: limitNum,
      totalCount,
      totalPages: Math.ceil(totalCount / limitNum),
      results: products
    });
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
                'imageurl', l.imageurl,
                'availabilitystatus', l.availabilitystatus
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

    let lowestPrice = null;
    if (hasListings) {
      const inStockListings = product.listings.filter(
        (l: any) => l.availabilitystatus === 'InStock' || l.availabilitystatus === 'Available'
      );
      const source = inStockListings.length > 0 ? inStockListings : product.listings;
      lowestPrice = source[0].price;
    }

    res.json({
      ...product,
      listings: hasListings ? product.listings : [],
      lowestPrice
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to fetch GPU' });
  }
};