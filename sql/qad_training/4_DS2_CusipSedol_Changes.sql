/*
	Training Query 4 - Datastream Cusip and Sedol Changes
	--------------------------------------------
	These queries map to Datastream and shows cusip and sedol history for a global ID.  Start and end dates in Ds2SedolChg and DS2CusipChg allow the user
	to find a sedol at a given point in time in history.
	
	MAINTENANCE LOG
	Date			Developer			Action		Notes
	------------------------------------------------------------------------------
	2013-11-13		ANONYMIZED_AUTHOR				CREATED
*/

-- QUERY 1 - CUSIPS
SELECT		G.ID 
	,	G.SECCODE
	,	G.NAME
	,	C.INFOCODE
	,	M.RANK
	,	C.STARTDATE
	,	C.ENDDATE
	,	C.CUSIP, d.infocode, d.DsQtName, M.VENCODE
FROM		SECMSTRX G
JOIN		SECMAPX M
	ON	M.SECCODE = G.SECCODE
	AND	M.VENTYPE = 33
	AND TYPE_ =1
	AND RANK = 1 -- VIEW ALL OR CURRENT ONLY
JOIN		DS2CUSIPCHG C		-- CUSIP CHANGES
	ON	C.INFOCODE = M.VENCODE
	join ds2ctryqtinfo d
	 on d.infocode = c.infocode 
WHERE G.ID = 'C'

-- QUERY 2 - SEDOLS
SELECT		G.ID AS ID
	,	G.SECCODE
	,	G.NAME
	,	C.INFOCODE
	,	M.RANK
	,	C.STARTDATE
	,	C.ENDDATE
	,	C.SEDOL
FROM		GSECMSTRX G
JOIN		GSECMAPX M
	ON	M.SECCODE = G.SECCODE
	AND	M.VENTYPE = 33
JOIN		DS2SEDOLCHG C
	ON	C.INFOCODE = M.VENCODE
WHERE		G.ID = '@GAMIN5'