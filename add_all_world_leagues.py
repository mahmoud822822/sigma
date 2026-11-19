p = "sigma_engine.py"
s = open(p).read()

start = s.find("    leagues = [")
end = s.find("    days =", start)
assert start != -1 and end != -1, "leagues list not found"

mega_leagues = '''    leagues = [
        # England & UK
        "eng.1","eng.2","eng.3","eng.4","eng.5","eng.fa","eng.league_cup","eng.trophy","eng.charity","eng.w.1",
        "sco.1","sco.2","sco.3","sco.4","sco.fa","sco.league_cup","wal.1","nir.1","irl.1",
        # Spain, Italy, Germany, France
        "esp.1","esp.2","esp.copa_del_rey","esp.super_cup","esp.w.1",
        "ita.1","ita.2","ita.3","ita.coppa_italia","ita.super_cup","ita.w.1",
        "ger.1","ger.2","ger.3","ger.dfb_pokal","ger.super_cup","ger.w.1",
        "fra.1","fra.2","fra.3","fra.coupe_de_france","fra.league_cup","fra.w.1",
        # Rest of Europe
        "por.1","por.2","por.taca","ned.1","ned.2","ned.cup","bel.1","bel.2","bel.cup",
        "tur.1","tur.2","tur.cup","gre.1","gre.cup","sui.1","sui.2","aut.1","aut.2",
        "den.1","den.2","swe.1","swe.2","nor.1","nor.2","fin.1","isl.1",
        "pol.1","pol.2","cze.1","svk.1","hun.1","rou.1","bul.1","cro.1","srb.1","svn.1","bih.1","mkd.1","alb.1","cyp.1","isr.1",
        "rus.1","rus.cup","ukr.1","blr.1","kaz.1","aze.1","arm.1","geo.1","ltu.1","lva.1","est.1",
        # UEFA Competitions
        "uefa.champions","uefa.champions_qual","uefa.europa","uefa.europa_qual","uefa.europa.conf","uefa.europa.conf_qual","uefa.nations","uefa.euro","uefa.euroq","uefa.super_cup","uefa.youth","uefa.wchampions",
        # Arab & Middle East Leagues
        "egy.1","egy.cup","ksa.1","ksa.2","ksa.kings_cup","uae.1","uae.cup","qat.1","qat.cup",
        "mar.1","tun.1","alg.1","lby.1","sdn.1","kuw.1","bhr.1","oma.1","jor.1","irq.1","lbn.1","syr.1","yem.1",
        # Africa & CAF
        "rsa.1","rsa.2","nga.1","gha.1","ken.1","uga.1","tan.1","zam.1","zim.1","eth.1","cmr.1","civ.1","sen.1","mli.1",
        "caf.champions","caf.confed","caf.nations","caf.nations_qual","caf.chan","caf.super_cup",
        # Asia & AFC
        "jpn.1","jpn.2","jpn.3","jpn.cup","kor.1","kor.2","chn.1","chn.2","aus.1","aus.w.1","nzl.1",
        "ind.1","ind.2","idn.1","tha.1","mys.1","sgp.1","vie.1","phi.1","irn.1","uzb.1",
        "afc.champions","afc.champions_two","afc.cup","afc.asian_cup","afc.worldq","aff.championship",
        # South America & CONMEBOL
        "bra.1","bra.2","bra.3","bra.copa_do_brasil","bra.paulista","bra.carioca",
        "arg.1","arg.2","arg.copa","col.1","col.2","chi.1","chi.2","per.1","uru.1","ecu.1","par.1","ven.1","bol.1",
        "conmebol.libertadores","conmebol.sudamericana","conmebol.recopa","conmebol.america",
        # North & Central America & CONCACAF
        "usa.1","usa.usl.1","usa.open","usa.nwsl","mex.1","mex.2","can.1","crc.1","hon.1","slv.1","gua.1","pan.1","jam.1",
        "concacaf.champions","concacaf.leagues_cup","concacaf.gold","concacaf.nations",
        # FIFA & International
        "fifa.world","fifa.worldq.uefa","fifa.worldq.caf","fifa.worldq.conmebol","fifa.worldq.afc","fifa.worldq.concacaf","fifa.worldq.ofc",
        "fifa.friendly","fifa.cwc","fifa.intercontinental","fifa.wwc","fifa.olympics","fifa.u20","fifa.u17"
    ]
'''

open(p, "w").write(s[:start] + mega_leagues + s[end:])
print("185+ WORLD LEAGUES ADDED OK")
