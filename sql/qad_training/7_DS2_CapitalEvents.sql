/*
DATASTREAM EQUITIES V2 - CAPITAL EVENTS EXAMPLE
--------------------------------------------

This query returns common items available for capital events, including spin-offs, takeovers, mergers, etc.
Source is Datastream V2.  Note the existence of the Resultant Code (ResInfoCode).  This field identifies
the entity that an acquired company merges into, or connects the spun-off company from the company doing the spinning.
Also note that EventNums are disparate.  For tracking a single transaction from rumor to proposed to effective, 
please consider the SDC Deals database.  

	MAINTENANCE LOG
	Date			Developer			Action		Notes
	------------------------------------------------------------------------------
	Jan 2012		ANONYMIZED_AUTHOR	Creation

-----------------------------------------------------------------------------------------
*/

SELECT MS.ID, MS.CUSIP, DS.INFOCODE, DS.DSCODE, DS.DSQTNAME, DC.EVENTNUM, DC.ACTIONTYPECODE, C1.DESC_ [ACT_DESC], 
	   DC.EVENTSTATUSCODE, C2.DESC_ [EVNT_DESC], DC.NUMOLDSHARES,
	   DC.NUMNEWSHARES, DC.CASHAMT, DC.OFFERCMPYNAME, DC.RESINFOCODE, 
	   DS2.DSQTNAME [RES_CMP_NAME], DC.EFFECTIVEDATE, DC.ANNOUNCEDDATE

FROM VW_SECURITYMASTERX MS
JOIN VW_DS2MAPPING MP
            ON MS.SECCODE = MP.SECCODE
			AND MS.TYP = MP.TYP

JOIN	DS2CTRYQTINFO DS
	ON		DS.INFOCODE = MP.VENCODE
JOIN	DS2CAPEVENT DC
	ON		DC.INFOCODE = DS.INFOCODE
JOIN	DS2XREF C1
	ON		C1.CODE = DC.ACTIONTYPECODE
	AND		C1.TYPE_ = 6
LEFT JOIN	DS2XREF C2
	ON		C2.CODE = DC.EVENTSTATUSCODE
	AND		C2.TYPE_ = 7

LEFT JOIN	DS2CTRYQTINFO DS2
	ON		DS2.INFOCODE = DC.RESINFOCODE
	
WHERE	MS.ID = 'SGP'

