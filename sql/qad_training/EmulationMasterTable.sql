SELECT        G.ID
       ,      G.SECCODE
       ,      G.NAME
       ,      C.*
       , d.infocode, d.DsQtName, M.VENCODE
FROM          SECMSTRX G
JOIN          SECMAPX M
       ON     M.SECCODE = G.SECCODE
       AND    M.VENTYPE = 33 -- Datastrema
       AND TYPE_ = 1 -- NorthAmer Equity
       AND RANK = 1 -- VIEW ALL OR CURRENT ONLY
JOIN          Ds2QtNameChg C             -- CUSIP CHANGES
       ON     C.INFOCODE = M.VENCODE
       join ds2ctryqtinfo d
       on d.infocode = c.infocode
WHERE G.ID = 'C'
 
