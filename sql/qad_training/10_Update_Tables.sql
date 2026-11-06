/*
	Training Query 10 - Update Log and Changes 
	--------------------------------------------
	The first query shows our update log.  This tracks all updates done to each table in the database.  The second query 
	shows one of the "_changes" tables.  Each table in the database has an "_changes" table associated with it.  This table
	shows *only* the contents of the most recently applied update.
	
	MAINTENANCE LOG
	Date			Developer			Action		Notes
	------------------------------------------------------------------------------
	2013-11-13		ANONYMIZED_AUTHOR				CREATED
*/ 

--- UPDATE TABLES ---
SELECT 
	*
FROM
		UPDATE_LOG
WHERE	TABLENAME = 'Ds2PrimQtPrc'
AND FILEDATE > GETDATE() - 30 -- EXAMPLE LAST 30 DAYS
ORDER BY FILEDATE DESC


-- EACH TABLE IN THE DATABASE HAS _CHANGES APPENDED TO IT, WHICH TRACKS THE UPDATES, ADDS, AND DELETES TO THE TABLE 
-- PER EACH UPDATE ON THAT TABLE, EXAMPLE:

SELECT * FROM Ds2PrimQtPrc_CHANGES