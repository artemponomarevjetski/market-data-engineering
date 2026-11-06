SELECT      C.StartDate
        ,   C.EndDate
        ,   G.ID
        ,   G.SECCODE
        ,   G.NAME
        ,   D.infocode, D.DsQtName, M.VENCODE
FROM        SECMSTRX G
JOIN        SECMAPX M
    ON      M.SECCODE = G.SECCODE
    AND     M.VENTYPE = 33          -- Datastrema
    AND     TYPE_ = 1               -- NorthAmer Equity
    AND     RANK = 1                -- VIEW ALL OR CURRENT ONLY
JOIN        Ds2QtNameChg C          -- CUSIP CHANGES
    ON      C.INFOCODE = M.VENCODE
JOIN        ds2ctryqtinfo D
    ON      D.infocode = C.infocode
WHERE       G.ID                                                      
IN ('A','AA','AAB','AAC','AACE','AADV','AAF','AAFG','AAG','GFR','AAGIY','AAGP','EVST','AAH','FILM','AAII;','AAI','AALA','AAM','AAN','ABN','AANB','AAON','AAP','AAPL')
ORDER BY    G.ID    
 
SELECT SECCODE, ID, Type_, NAME, Country FROM SecMstrX WHERE ID 
IN ('A','AA','AAB','AAC','AACE','AADV','AAF','AAFG','AAG','GFR','AAGIY','AAGP','EVST','AAH','FILM','AAII;','AAI','AALA','AAM','AAN','ABN','AANB','AAON','AAP','AAPL')

SELECT ID, SECCODE FROM SECMSTRX WHERE ID   
IN ('A','AA','AAB','AAC','AACE','AADV','AAF','AAFG','AAG','GFR','AAGIY','AAGP','EVST','AAH','FILM','AAII;','AAI','AALA','AAM','AAN','ABN','AANB','AAON','AAP','AAPL')

SELECT * FROM SECMAPX WHERE SECCODE = 29629 AND VENTYPE = 33 --Ventype is Datastream

SELECT DISTINCT VENTYPE FROM SECMAPX

SELECT DISTINCT 'How many symbols in my universe = ', COUNT(SECCODE) FROM SECMAPX

SELECT VENTYPE, VENNAME FROM SECVENTYPE WHERE VENTYPE = 33

SELECT      M.ID
        ,   M.[NAME]
        ,   P.*
FROM        SECMSTRX M 
JOIN        SECMAPX P
    ON      M.SECCODE = P.SECCODE   AND   M.TYPE_ = 1   AND P.VENTYPE = 10 --Worldscope
    WHERE   M.ID
IN ('A','AA','AAB','AAC','AACE','AADV','AAF','AAFG','AAG','GFR','AAGIY','AAGP','EVST','AAH','FILM','AAII;','AAI','AALA','AAM','AAN','ABN','AANB','AAON','AAP','AAPL')

SELECT      A.ID    AS  TRQID,  A.Name,     C.Ticker,       D.*
FROM        SecMstrX A
JOIN        RDCSecMapX B
    ON      A.SecCode = B.SecCode
    AND     B.VenType = 55
    AND     A.Type_ = 1
    AND     exchange = 1
JOIN        RDCQuoteInfo C
    ON      B.VenCode = C.QuoteID
JOIN        RDCRICData D
    ON      C.QuoteID = D.QuoteID
WHERE       A.ID
IN  ('A','AA','AAB','AAC','AACE','AADV','AAF','AAFG','AAG','GFR','AAGIY','AAGP','EVST','AAH','FILM','AAII;','AAI','AALA','AAM','AAN','ABN','AANB','AAON','AAP','AAPL')    
ORDER BY    A.ID