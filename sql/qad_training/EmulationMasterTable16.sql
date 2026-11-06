SELECT  COUNT(DISTINCT SECCODE)     AS 'How many symbols in my universe'            FROM    SECMAPX

SELECT  COUNT(DISTINCT  VENTYPE)    AS 'How many distinct vendors in QA  Direct'    FROM    SECMAPX

SELECT DISTINCT         VENTYPE     AS 'List all vendors'                           FROM    SECMAPX

SELECT                  VENTYPE     AS 'Correspondence between  VENTYPE', VENNAME   FROM    SECVENTYPE      WHERE VENTYPE = 33

SELECT * FROM           SECMAPX     WHERE   SECCODE = 29629 AND VENTYPE = 33        --Ventype is Datastream

SELECT
                D.STARTDATE AS 'From'
        ,       D.ENDDATE   AS 'To'
        ,       C.Ticker
        ,       A.Name
        ,       A.*, B.*, C.*, D.*, M.*, L.*, K.*

FROM        SecMstrX        A
            
JOIN        RDCSecMapX      B
        ON                      A.SecCode = B.SecCode
  --      AND                     B.VenType = 55
 --       AND                     A.Type_ = 1
  --      AND                     exchange = 1

JOIN        RDCQuoteInfo    C
        ON                      B.VenCode = C.QuoteID

JOIN        RDCRICData      D
        ON                      C.QuoteID = D.QuoteID

JOIN        SECMAPX         M
        ON                      M.SECCODE = A.SECCODE
        AND                     M.VENTYPE = 33          -- Datastream
        AND                     TYPE_ = 1               -- NorthAmer Equity
        AND                     M.RANK = 1              -- VIEW ALL OR CURRENT ONLY
    -- or use b.rank

JOIN        Ds2QtNameChg    K                           -- CUSIP CHANGES
        ON                      K.INFOCODE = M.VENCODE

JOIN        ds2ctryqtinfo   L
        ON                      L.infocode = K.infocode

--JOIN        prc.PRCINFO N
  --      ON                      N.SecType = 'A'

WHERE       C.TICKER
        IN  (
            'BABA'
           
        )
   --     AND A.COUNTRY = 'USA'
ORDER BY    C.TICKER