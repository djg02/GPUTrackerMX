-- DROP SCHEMA public;

CREATE SCHEMA public AUTHORIZATION pg_database_owner;

COMMENT ON SCHEMA public IS 'standard public schema';

-- DROP SEQUENCE public.listing_listingid_seq;

CREATE SEQUENCE public.listing_listingid_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.listing_parsed_listingparsedid_seq;

CREATE SEQUENCE public.listing_parsed_listingparsedid_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.pricesnapshot_snapshotid_seq;

CREATE SEQUENCE public.pricesnapshot_snapshotid_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.product_listing_match_matchid_seq;

CREATE SEQUENCE public.product_listing_match_matchid_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.product_productid_seq;

CREATE SEQUENCE public.product_productid_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.product_sku_productskuid_seq;

CREATE SEQUENCE public.product_sku_productskuid_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;
-- DROP SEQUENCE public.store_storeid_seq;

CREATE SEQUENCE public.store_storeid_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;-- public.product definition

-- Drop table

-- DROP TABLE public.product;

CREATE TABLE public.product (
	productid int8 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL,
	producttype varchar(255) NULL,
	canonicalname varchar(255) NULL,
	brand varchar(255) NULL,
	model varchar(255) NULL,
	manufacturer varchar(255) NULL,
	series varchar(255) NULL,
	oc bool NULL,
	vramgb numeric(4, 1) NULL,
	memorytype varchar(255) NULL,
	buswidth int4 NULL,
	interfaceversion varchar(255) NULL,
	color varchar(255) NULL,
	fans int4 NULL,
	boostclock int4 NULL,
	baseclock int4 NULL,
	createdat timestamp DEFAULT now() NULL,
	coolervariant varchar(255) NULL,
	CONSTRAINT product_pkey PRIMARY KEY (productid)
);


-- public.store definition

-- Drop table

-- DROP TABLE public.store;

CREATE TABLE public.store (
	storeid int8 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL,
	storename varchar(255) NULL,
	CONSTRAINT store_pkey PRIMARY KEY (storeid)
);


-- public.listing definition

-- Drop table

-- DROP TABLE public.listing;

CREATE TABLE public.listing (
	listingid int8 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL,
	productid int8 NULL,
	storeid int8 NOT NULL,
	storetitle varchar(500) NULL,
	link varchar(1000) NULL,
	availabilitystatus varchar(100) NULL,
	createdat timestamp NULL,
	updatedat timestamp NULL,
	lastseenat timestamp NULL,
	currentprice numeric(18, 2) NULL,
	currentpriceupdatedat timestamp NULL,
	imageurl varchar(1000) NULL,
	stockamount int4 NULL,
	rawjson jsonb NULL,
	currency varchar(1000) NULL,
	storelistingid varchar(1000) NULL,
	shippingprice int4 NULL,
	parsed bool DEFAULT false NULL,
	parsedat timestamp NULL,
	specjson json NULL,
	CONSTRAINT listing_pkey PRIMARY KEY (listingid),
	CONSTRAINT uq_listing_store_external UNIQUE (storeid, storelistingid),
	CONSTRAINT fk_listing_product FOREIGN KEY (productid) REFERENCES public.product(productid),
	CONSTRAINT fk_listing_store FOREIGN KEY (storeid) REFERENCES public.store(storeid)
);


-- public.listing_parsed definition

-- Drop table

-- DROP TABLE public.listing_parsed;

CREATE TABLE public.listing_parsed (
	listingparsedid bigserial NOT NULL,
	canonicalid int8 NULL,
	manufacturer text NULL,
	chipset_brand text NULL,
	gpumodel text NULL,
	series text NULL,
	oc bool NULL,
	vramgb numeric(4, 1) NULL,
	memorytype text NULL,
	buswidth int4 NULL,
	interfaceversion text NULL,
	coolervariant text NULL,
	color text NULL,
	sku text NULL,
	parsedat timestamp DEFAULT now() NULL,
	title varchar(255) NULL,
	fans int4 NULL,
	boostclock int4 NULL,
	baseclock int4 NULL,
	listingid int8 NULL,
	product_normalized bool DEFAULT false NOT NULL,
	CONSTRAINT listing_parsed_listingid_unique UNIQUE (listingid),
	CONSTRAINT listing_parsed_pkey PRIMARY KEY (listingparsedid),
	CONSTRAINT fk_listing FOREIGN KEY (listingid) REFERENCES public.listing(listingid),
	CONSTRAINT listing_parsed_canonicalid_fkey FOREIGN KEY (canonicalid) REFERENCES public.product(productid)
);


-- public.pricesnapshot definition

-- Drop table

-- DROP TABLE public.pricesnapshot;

CREATE TABLE public.pricesnapshot (
	snapshotid int8 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL,
	listingid int8 NOT NULL,
	currency varchar(10) NULL,
	price numeric(18, 2) NULL,
	capturedat timestamp NULL,
	shippingprice int4 NULL,
	CONSTRAINT pricesnapshot_pkey PRIMARY KEY (snapshotid),
	CONSTRAINT fk_pricesnapshot_listing FOREIGN KEY (listingid) REFERENCES public.listing(listingid)
);


-- public.product_listing_match definition

-- Drop table

-- DROP TABLE public.product_listing_match;

CREATE TABLE public.product_listing_match (
	matchid bigserial NOT NULL,
	productid int8 NOT NULL,
	listingid int8 NOT NULL,
	matchmethod varchar(50) NOT NULL,
	confidence numeric(5, 2) NOT NULL,
	createdat timestamp DEFAULT now() NULL,
	CONSTRAINT product_listing_match_pkey PRIMARY KEY (matchid),
	CONSTRAINT uq_listing_match UNIQUE (listingid),
	CONSTRAINT product_listing_match_listingid_fkey FOREIGN KEY (listingid) REFERENCES public.listing(listingid),
	CONSTRAINT product_listing_match_productid_fkey FOREIGN KEY (productid) REFERENCES public.product(productid)
);


-- public.product_sku definition

-- Drop table

-- DROP TABLE public.product_sku;

CREATE TABLE public.product_sku (
	productskuid bigserial NOT NULL,
	productid int8 NOT NULL,
	sku text NOT NULL,
	normalizedsku text NOT NULL,
	createdat timestamp DEFAULT now() NULL,
	CONSTRAINT product_sku_pkey PRIMARY KEY (productskuid),
	CONSTRAINT uq_product_sku_normalized UNIQUE (normalizedsku),
	CONSTRAINT product_sku_productid_fkey FOREIGN KEY (productid) REFERENCES public.product(productid)
);
CREATE UNIQUE INDEX idx_product_sku_normalized ON public.product_sku USING btree (normalizedsku);