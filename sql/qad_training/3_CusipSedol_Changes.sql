/*
	Training Query 3 - Cusip and Sedol Changes
	--------------------------------------------
	History of Cusip and Sedols of record for select IDs from our Core Schema security master tables.
	
	MAINTENANCE LOG
	Date			Developer			Action		Notes
	------------------------------------------------------------------------------
	2016-01-28		ANONYMIZED_AUTHOR				CREATED
*/



-- QUERY 1 :  NORTH AMERICAN CUSIP HISTORY

SELECT X.SECCODE, X.ID, X.NAME, X.TYP, C.STARTDATE, C.ENDDATE, C.CUSIP 

FROM vw_securityMasterX X 
JOIN SECCSPCHGX C
ON X.SECCODE = C.SECCODE
AND X.TYP = 1 -- NORTH AMERICA

WHERE ID = 'C'

-- QUERY 2 : GLOBAL SEDOL HISTORY
SELECT X.SECCODE, X.ID, X.NAME, X.TYP, C.STARTDATE, C.ENDDATE, C.SEDOL 

FROM vw_securityMasterX X 
JOIN GSECSDLCHG C
ON X.SECCODE = C.SECCODE
AND X.TYP = 6 -- GLOBAL

WHERE ID = '@GAMIN5'


-- QUERY 3 :  NORTH AMERICAN SEDOL HISTORY

SELECT X.SECCODE, X.ID, X.NAME, X.TYP, C.STARTDATE, C.ENDDATE, C.SEDOL 

FROM vw_securityMasterX X 
JOIN SECSDLCHGX C  -- OR SECSDL2CHGX FOR DUALLY LISTED
ON X.SECCODE = C.SECCODE
AND X.TYP = 1 -- NORTH AMERICA

WHERE ID = '88706M10' -- TIM HORTONS



