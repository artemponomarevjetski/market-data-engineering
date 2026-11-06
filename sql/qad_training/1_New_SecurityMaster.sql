/*
	Training Query 1 - Security Master
	--------------------------------------------
	These queries show a record from each of our master security tables.  The ID field is unique across both
	sets, while the SecCode is unique within region (North America vs Global).
	
	MAINTENANCE LOG
	Date			Developer			Action		Notes
	------------------------------------------------------------------------------
	2016-01-28		ANONYMIZED_AUTHOR				CREATED
*/


-- QUERY 1:  REGIONAL SECURITY MASTER

SELECT SECCODE, ID, TYPE_, CUSIP, SEDOL, SEDOL2, ISIN, NAME, COUNTRY FROM SECMSTRX WHERE ID = 'TOC'
SELECT SECCODE, ID, TYPE_, CUSIP, SEDOL, SEDOL2, ISIN, NAME, COUNTRY FROM GSECMSTRX WHERE ID = '@HONDA9'

-- QUERY 2:  COMBINE REGIONS;  -- UNIQUE IDENTIFIER IS SECCODE + TYP

;WITH MASTERX AS
(
	SELECT 1 AS TYP
			,*
	FROM SECMSTRX
	WHERE TYPE_ = 1 -- EQUITIES
				UNION ALL
	SELECT 6 AS TYP
			,*
	FROM GSECMSTRX
	WHERE TYPE_ = 10 -- EQUITIES
)
SELECT SECCODE, TYP, ID, CUSIP, SEDOL, SEDOL2, ISIN, NAME, COUNTRY

FROM MASTERX A
WHERE ID IN ('TOC', '@HONDA9')

-- QUERY 3 :  VIEW

SELECT * FROM vw_securityMasterX WHERE ID IN ('TOC', '@HONDA9') 



