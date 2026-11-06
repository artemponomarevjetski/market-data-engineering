SELECT      G.ID
        ,   C.*
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
    
WHERE G.ID IN ('C', 'BAC')
 
SELECT      A.ID    AS  TRQID,  A.Name,     C.Ticker,       D.*
FROM        SecMstrX A
JOIN        RDCSecMapX B
    ON      A.SecCode = B.SecCode
    AND     B.VenType = 55
    AND     A.Type_ = 1
    AND     exchange = 1
JOIN        RDCQuoteInfo C
    ON      B.VenCode = C.QuoteID
JOIN        RDCRICData  D
    ON  A.ID IN ('AAII', 'AAM', 'AAON', 'AA', 'MSFT', 'AAPL', 'CSX', 'LUV', 'SNAP', 'BTO')
ORDER BY A.ID