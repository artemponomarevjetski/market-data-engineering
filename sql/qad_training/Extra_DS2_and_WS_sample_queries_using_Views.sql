/*
	Training Query - Adoption of  Views
	--------------------------------------------
	
        THE BELOW QUERIES DESINGED TO DEMONSTARTE THE BENEFITS OF OUR VIEWS FUNCTIONALITIES.

	
	MAINTENANCE LOG
	Date			Developer			Action		Notes
	------------------------------------------------------------------------------
                                                  UNKNOWN	

*/ 




--Vodafone pricing in Datastream
select aa.*, cc.*, dd.*
from vw_SecurityMasterX aa
join vw_SecurityMappingX bb
	on aa.seccode = bb.seccode
	and aa.typ = bb.typ
	and bb.ventype = 33
	and bb.rank = 1
join vw_Ds2SecInfo cc
	on cc.Infocode = bb.vencode
join vw_Ds2Pricing dd
	on dd.infocode = cc.infocode
	and dd.adjtype = 2
	and dd.exchintcode = cc.primexchintcode
where aa.id = '@vodaf1'
order by dd.marketdate


--Vodafone Market Cap in Datastream
select aa.*, cc.*, dd.*
from vw_SecurityMasterX aa
join vw_SecurityMappingX bb
	on aa.seccode = bb.seccode
	and aa.typ = bb.typ
	and bb.ventype = 33
	and bb.rank = 1
join vw_Ds2SecInfo cc
	on cc.Infocode = bb.vencode
join vw_Ds2MktCap dd
	on dd.infocode = cc.infocode
where aa.id = '@vodaf1'
order by dd.marketdate


--Vodafone company classification in Worldscope
select aa.*, cc.*
from vw_SecurityMasterX aa
join vw_SecurityMappingX bb
	on aa.seccode = bb.seccode
	and aa.typ = bb.typ
	and bb.ventype = 10
	and bb.rank = 1
join vw_WSCompanyInfo cc
	on cc.code = bb.vencode
where aa.id = '@vodaf1'


--Vodafone item 1001 in Worldscope
select aa.*, dd.*
from vw_SecurityMasterX aa
join vw_SecurityMappingX bb
	on aa.seccode = bb.seccode
	and aa.typ = bb.typ
	and bb.ventype = 10
	and bb.rank = 1
join vw_WSCompanyInfo cc
	on cc.code = bb.vencode
join vw_WSItemData dd
	on dd.code = cc.code
	and dd.item = 1001
	and dd.freq = 'a'
where aa.id = '@vodaf1'
order by fiscalperiodenddate 


--From GBP to USD sport rate
select *
from vw_Ds2FxCross aa
where aa.fromcurrcode = 'gbp'
	and aa.tocurrcode = 'usd'
	and aa.ratetype = 'spot'
order by aa.exratedate 









