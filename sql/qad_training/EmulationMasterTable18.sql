SELECT  COUNT(DISTINCT SECCODE)     AS 'How many symbols in my universe'            FROM    SECMAPX

SELECT  COUNT(DISTINCT  VENTYPE)    AS 'How many distinct vendors in QA  Direct'    FROM    SECMAPX

SELECT DISTINCT         VENTYPE     AS 'List all vendors'                           FROM    SECMAPX

SELECT                  VENTYPE     AS 'Correspondence between  VENTYPE', VENNAME   FROM    SECVENTYPE      WHERE VENTYPE = 33

SELECT * FROM           SECMAPX     WHERE   SECCODE = 29629 AND VENTYPE = 33        --Ventype is Datastream

SELECT
                  A.SecCode
          ,       A.ID
          ,       A.Type_
          ,       A.Idbase
          ,       A.IdSeq
          ,       A.NAME
          ,       A.Country
          ,       A.Vendors1,       A.Vendors2,       A.Vendors3,       A.Vendors4
          ,       B.SecCode
          ,       B.Ventype
          ,       B.VenCode
          ,       B.Rank
          ,       B.Exchange
          ,       B.StartDate
          ,       B.EndDate
          ,       C.QuoteID,C.QuoteStatusCode,C.QuoteType,C.QuoteCatCode,C.ComName,C.IsSuspended,C.QuoteISOCurrCode,C.QuoteGrpByPsExch,C.QuoteCla,C.RateTypeCode,C.RSCAssetCla,C.ShortName,C.TagCla,C.InstrID,C.Mic,C.Opol,C.Ticker,C.TMTPermId,C.GemPermId
          ,      D.QuoteID,D.SeqNo,D.StartDate,D.StartTime,D.EndDate,D.EndTime,D.RIC 
          ,       M.SecCode,M.VenType,M.VenCode,M.Rank,M.Exchange,M.StartDate,M.EndDate
      ,     L.InfoCode,L.DsCode,L.DsSecCode,L.Region,L.RegCodeTypeId,L.IsPrimQt,L.DsQtName,L.DsLocalCode,L.DsMnem,L.CovergCode,L.StatusCode,L.PermID,L.TypeCode,L.PrimISOCurrCode,L.DelistDate
       ,     K.InfoCode,K.StartDate,K.EndDate,K.DSQtName

FROM        SecMstrX        A

--JOIN prc.PRCINFO AA
  --ON                      A.SecCode = AA.SecCode
            
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
--        AND                     M.VENTYPE = 33          -- Datastream
 --       AND                     TYPE_ = 1               -- NorthAmer Equity
 --       AND                     M.RANK = 1              -- VIEW ALL OR CURRENT ONLY
    -- or use b.rank

JOIN        Ds2QtNameChg    K                           -- CUSIP CHANGES
        ON                      K.INFOCODE = M.VENCODE

JOIN        ds2ctryqtinfo   L
        ON                      L.infocode = K.infocode

--JOIN        prc.PRCINFO N
  --      ON                      N.SecType = 'A'

--WHERE       C.TICKER
  --      IN  ('AAB'    ,
        --    'BABA' 
    --    )
   --     AND A.COUNTRY = 'USA'
   WHERE      A.NAME LIKE '%ASTRA AB%' 
--AND 
--A.NAME LIKE '%A%'
ORDER BY      C.TICKER