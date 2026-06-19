import { Request, Response } from 'express';
import pool from '../db';

function addCondition(
  conditions: string[],
  values: any[],
  param: any,
  sqlFragment: (placeholder: string) => string,
  transform: (val: any) => any = (val) => val
) {
  if (param !== undefined && param !== '') {
    values.push(transform(param));
    conditions.push(sqlFragment(`$${values.length}`));
  }
}

function addArrayCondition(
  conditions: string[],
  values: any[],
  param: any[],
  sqlFragment: (placeholder: string) => string
) {
  if (param && param.length > 0) {
    values.push(param)
    conditions.push(sqlFragment(`$${values.length}`))
  }
}

function toArray(param: any): string[] {
  if (!param) return []
  if (Array.isArray(param)) return param as string[]
  return [param as string]
}

export const getAllGpus = async (req: Request, res: Response) => {
   const {
    brand, vram, maxPrice, minPrice, manufacturer, color, inStock,
    model, memorytype, oc, buswidth, fans, interfaceversion, boostclock,
    page = '1', limit = '20', sort, search
  } = req.query;

    const pageNum = Number(page);
    const limitNum = Number(limit);

    if (isNaN(pageNum) || pageNum < 1) {
      return res.status(400).json({ error: 'Invalid page parameter. Must be a positive integer.' });
    }

    if (isNaN(limitNum) || limitNum < 1 || limitNum > 50) {
      return res.status(400).json({ error: 'Invalid limit parameter. Must be between 1 and 50.' });
    }

    let minPriceNum: number | undefined;
    let maxPriceNum: number | undefined;

    if (minPrice !== undefined) {
      minPriceNum = Number(minPrice);
      if (isNaN(minPriceNum) || minPriceNum < 0) {
        return res.status(400).json({ error: 'Invalid minPrice parameter. Must be a non-negative number.' });
      }
    }

    if (maxPrice !== undefined) {
      maxPriceNum = Number(maxPrice);
      if (isNaN(maxPriceNum) || maxPriceNum < 0) {
        return res.status(400).json({ error: 'Invalid maxPrice parameter. Must be a non-negative number.' });
      }
    }

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
    const brandArr = toArray(brand)
    const manufacturerArr = toArray(manufacturer)
    const modelArr = toArray(model)
    const memorytypeArr = toArray(memorytype)
    const colorArr = toArray(color)
    const fansArr = toArray(fans)
    const buswidthArr = toArray(buswidth)
    const interfaceversionArr = toArray(interfaceversion)
    const vramArr = toArray(vram)

    addArrayCondition(conditions, values, brandArr, p => `p.brand = ANY(${p})`);
    addArrayCondition(conditions, values, manufacturerArr, p => `p.manufacturer_normalized = ANY(${p})`);
    addArrayCondition(conditions, values, modelArr, p => `p.model_normalized = ANY(${p})`);
    addArrayCondition(conditions, values, memorytypeArr, p => `p.memorytype = ANY(${p})`);
    addArrayCondition(conditions, values, colorArr, p => `p.color = ANY(${p})`);
    addArrayCondition(conditions, values, fansArr, p => `p.fans = ANY(${p}::int[])`);
    addArrayCondition(conditions, values, buswidthArr, p => `p.buswidth = ANY(${p}::int[])`);
    addArrayCondition(conditions, values, interfaceversionArr, p => `p.interfaceversion = ANY(${p})`);
    addArrayCondition(conditions, values, vramArr, p => `p.vramgb::text = ANY(${p})`);

    addCondition(havingConditions, values, maxPriceNum, p => 
      `MIN(l.currentprice) FILTER (WHERE l.availabilitystatus IN ('InStock', 'Available')) <= ${p}`);
    addCondition(havingConditions, values, minPriceNum, p => 
      `MIN(l.currentprice) FILTER (WHERE l.availabilitystatus IN ('InStock', 'Available')) >= ${p}`);

    if (oc !== undefined) {
      values.push(oc === 'true');
      conditions.push(`p.oc = $${values.length}`);
    }

    if (inStock === 'true') {
      havingConditions.push(`COUNT(*) FILTER (WHERE l.availabilitystatus IN ('InStock', 'Available')) > 0`);
    }

    if (search) {
      const words = (search as string).trim().split(/\s+/);
      words.forEach(word => {
        values.push(`%${word}%`);
        conditions.push(`p.canonicalname ILIKE $${values.length}`);
      });
}

    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    const havingClause = havingConditions.length > 0 ? `HAVING ${havingConditions.join(' AND ')}` : '';

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
            p.boostclock,
            p.color,
            p.oc,
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

    const products = result.rows.map((product: any) => {
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
            p.oc,
            p.boostclock,
            p.baseclock,
            json_agg(
                json_build_object(
                'storename', s.storename,
                'price', l.currentprice,
                'shipping', l.shippingprice,
                'currency', l.currency,
                'link', l.link,
                'imageurl', l.imageurl,
                'availabilitystatus', l.availabilitystatus,
                'lastseen', l.lastseenat,
                'currentpriceupdated', l.currentpriceupdatedat
                ) ORDER BY (l.currentprice + COALESCE(l.shippingprice, 0)) ASC
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

export const getGpuFilters = async (req: Request, res: Response) => {
  try {
    const [brandsResult, manufacturersResult, colorsResult, vramResult, modelResult, fansResult, memoryTypeResult, ocResult, buswidthResult, interfaceVersionResult ] = await Promise.all([
          pool.query(`SELECT DISTINCT brand FROM product WHERE brand IS NOT NULL ORDER BY brand`),
          pool.query(`SELECT DISTINCT manufacturer_normalized FROM product WHERE manufacturer_normalized IS NOT NULL ORDER BY manufacturer_normalized`),
          pool.query(`SELECT DISTINCT color FROM product WHERE color IS NOT NULL ORDER BY color`),
          pool.query(`SELECT DISTINCT vramgb FROM product WHERE vramgb IS NOT NULL ORDER BY vramgb`),
          pool.query(`SELECT DISTINCT model_normalized FROM product WHERE model_normalized IS NOT NULL ORDER BY model_normalized`),
          pool.query(`SELECT DISTINCT fans FROM product WHERE fans IS NOT NULL ORDER BY fans`),
          pool.query(`SELECT DISTINCT memorytype FROM product WHERE memorytype IS NOT NULL ORDER BY memorytype`),
          pool.query(`SELECT DISTINCT oc FROM product WHERE oc IS NOT NULL ORDER BY oc`),
          pool.query(`SELECT DISTINCT buswidth FROM product WHERE buswidth IS NOT NULL ORDER BY buswidth`),
          pool.query(`SELECT DISTINCT interfaceversion FROM product WHERE interfaceversion IS NOT NULL ORDER BY interfaceversion`)
        ]);

        res.json({
          brands: brandsResult.rows.map((r: any) => r.brand),
          manufacturers: manufacturersResult.rows.map((r: any) => r.manufacturer_normalized),
          colors: colorsResult.rows.map((r: any) => r.color),
          vramOptions: vramResult.rows.map((r: any) => r.vramgb),
          models: modelResult.rows.map((r: any) => r.model_normalized),
          fans: fansResult.rows.map((r: any) => r.fans),
          memoryTypes: memoryTypeResult.rows.map((r: any) => r.memorytype),
          ocOptions: ocResult.rows.map((r: any) => r.oc),
          buswidths: buswidthResult.rows.map((r: any) => r.buswidth),
          interfaceVersions: interfaceVersionResult.rows.map((r: any) => r.interfaceversion)
        });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to fetch filters' });
  }
};