Select  A.ID as TRQID, A.Name, C.Ticker, D.*
from SecMstrX A
       JOIN   RDCSecMapX B
              on a.SecCode = b.SecCode
              and b.VenType = 55
              and a.Type_ = 1
              and exchange = 1
       JOIN   RDCQuoteInfo c
              on b.VenCode = c.QuoteID  
       JOIN   RDCRICData D
              on c.QuoteID = D.QuoteID
where a.id  in ('AAII', 'AAM', 'AAON', 'AA', 'MSFT', 'AAPL', 'CSX', 'LUV', 'SNAP', 'BTO')
order by a.Id
 
