/*
	Training Query 8 - Complete Issue List
	--------------------------------------------
	This query returns all issues, globally, and their respective TQA IDs for a given issuer code (ISRCODE).
	
	MAINTENANCE LOG
	Date			Developer			Action		Notes
	------------------------------------------------------------------------------
	2016-1-28						CREATED
*/

SELECT 	ISR.ISRCODE
	,	ISR.ISRNAME
	,	X.ID
	,	X.SECCODE
	,	X.NAME
	,	X.SEDOL
	,	X.CUSIP
	,	I.RANK
	,	X.TYP -- REGION
	
FROM 		QAI.PRC.PRCISR ISR
	JOIN	QAI.PRC.PRCISS I
		ON	I.ISRCODE = ISR.ISRCODE
		AND	I.TYPE_ IN (1,6) -- Eliminates Fixed Income issues (20)
	LEFT JOIN	VW_SECURITYMASTERX X
		ON X.SECCODE = I.CODE
		AND X.TYP = I.TYPE_
WHERE		ISR.ISRCODE = 52712 -- Microsoft
ORDER BY	I.RANK