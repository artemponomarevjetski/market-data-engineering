/*
	Training Query 2 - Security Mapping
	--------------------------------------------
	All queries illustrate how to join the mapping tables.  The first example is for North America and shows a mapping to
	Datastream.	The second query shows a dually listed example to illustrate the meaning behind Exchange.  The third
	example shows a Global set of securities and highlights our Rank for expanded historical mapping.  Query 4 leverages
	the SQL Views to show all mappings for a particular ID.
	
	MAINTENANCE LOG
	Date			Developer			Action		Notes
	------------------------------------------------------------------------------
	2016-01-28		ANONYMIZED_AUTHOR				CREATED
*/



-- QUERY 1 :  NORTH AMERICAN MAPPING
SELECT
	M.Id
,	M.[Name]
,	M.CUSIP
,	P.*
FROM
		SECMSTRX M
JOIN	SECMAPX P
	ON	M.SECCODE = P.SECCODE
	AND M.TYPE_ = 1
	--AND P.VENTYPE = 33 --Datastream

WHERE M.ID = 'GE' 

-- QUERY 2:  DUALLY LISTED
SELECT
	M.Id
,	M.[Name]
,	M.CUSIP
,	M.SEDOL
,	M.SEDOL2
,	P.*
FROM
		SECMSTRX M
JOIN	SECMAPX P
	ON	M.SECCODE = P.SECCODE
	AND M.TYPE_ = 1
	--AND P.VENTYPE = 33 --Datastream

WHERE M.ID = 'TOC' 

-- QUERY 3:  SHOW ALL

SELECT
	M.Id
,	M.SECCODE
,	M.SEDOL
,	M.[Name]
,	P.RANK, P.VENCODE, P.VENTYPE, V.VENNAME, P.STARTDATE, P.ENDDATE

FROM
		GSECMSTRX M
JOIN	GSECMAPX P
	ON	M.SECCODE = P.SECCODE 
JOIN	SECVENTYPE V
ON		V.VENTYPE = P.VENTYPE
WHERE ID IN ('@HONDA9', '@PATNI1')
AND V.VENTYPE != 30 

-- QUERY 4:  VIEW

SELECT	M.ID, M.SECCODE, M.SEDOL, M.NAME, MP.RANK, MP.VENCODE ,MP.VENTYPE, V.VENNAME, MP.STARTDATE, MP.ENDDATE

FROM		VW_SECURITYMASTERX M
JOIN		VW_SECURITYMAPPINGX MP
ON		MP.SECCODE = M.SECCODE
AND		M.TYP = MP.TYP
JOIN		SECVENTYPE V
ON		V.VENTYPE = MP.VENTYPE

WHERE		M.SEDOL = '643514' AND MP.VENTYPE != 30

