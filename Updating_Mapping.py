import requests as r
from bs4 import BeautifulSoup
import pandas as pd
import re
import folium
import geopandas as gpd
from datetime import datetime as dt,date,timedelta
import numpy as np
from branca.element import Template, MacroElement
import sqlalchemy


DATA_PATH=r"C:\Users\timna\Covid_WebSite\Data\Covid19_{}.xlsx"
DATA_GPATH=r"C:\Users\timna\OneDrive\Документы\Covid19_Tatarstan\Data\Covid19_{}.xlsx"

MAP_PATH=r"C:/Users/timna/Covid_WebSite/Maps/index_{}.html"
MAP_GPATH=r"C:/Users/timna/OneDrive/Документы/Covid19_Tatarstan/Maps/index_{}.html"

PHP_PATH=r"C:\Users\timna\OneDrive\Документы\Covid19_Tatarstan\index.php"

def add_overhidden():
    with open(MAP_PATH.format(dt.now().strftime("%d.%m.%Y"))) as f:
        new_text=f.read().replace("<body>","<body style=overflow-y:hidden>")
    with open(MAP_PATH.format(dt.now().strftime("%d.%m.%Y")), "w") as f:
        f.write(new_text)
    with open(MAP_GPATH.format(dt.now().strftime("%d.%m.%Y"))) as f:
        new_text=f.read().replace("<body>","<body style=overflow-y:hidden>")
    with open(MAP_GPATH.format(dt.now().strftime("%d.%m.%Y")), "w") as f:
        f.write(new_text)


def mapping(covid_data):
    geo_data=gpd.read_file(r"C:\Users\timna\Russia_geojson_OSM\GeoJson's\Regions\PFO\Республика Татарстан_Tatarstan.geojson")
    covid_data["Район"]=[i+" район" if i not in ["Казань","Набережные Челны"] else "городской округ "+i for i in covid_data["Район"]]
    final_data=geo_data.merge(covid_data,right_on='Район',left_on='district')[["district","geometry","Случаи","Прирост"]]
    m=folium.Map([55.257670, 51.355722],zoom_start=7,zoom_control=False,
               scrollWheelZoom=False,
                max_zoom=7,
                min_zoom=7,
               dragging=False,
               double_click_zoom=False,
               tiles="https://{s}.tile.jawg.io/jawg-light/{z}/{x}/{y}{r}.png?access-token=LvQFAfvNKy1k8ZdbZbh1nZthL9k4YukhhC9kJX5f2wOby0fMzVn3osslwu8vkGoy",attr='<a href="http://jawg.io" title="Tiles Courtesy of Jawg Maps" target="_blank" class="jawg-attrib">&copy; <b>Jawg</b>Maps</a> | <a href="https://www.openstreetmap.org/copyright" title="OpenStreetMap is open data licensed under ODbL" target="_blank" class="osm-attrib">&copy; OSM contributors</a>')
              
    q=list(np.quantile(final_data["Случаи"],[0.25,0.5,0.75,0.95]))
    palette=[]
    for val in final_data.itertuples():
        if val[-2]<q[0]:
            palette.append("#19ff19")
        elif val[-2]>=q[0] and val[-2]<q[1]:
            palette.append("#faa307")
        elif val[-2]>=q[1] and val[-2]<q[2]:
            palette.append("#e85d04")
        elif val[-2]>=q[2] and val[-2]<q[3]:
            palette.append("#DC143C")
        elif val[-2]>=q[3]:
            palette.append("#ff0000")

    final_data["Прирост"]=['<b style="color: red; font-size: 15px;">↑{}</b>'.format(i) if i>0 else "" for i in final_data["Прирост"].values]
    final_data["Color"]=palette
    final_data["district"]="<b>"+final_data["district"]+"</b>"
    final_data["Случаи"]="Случаев:"+"<b>"+final_data["Случаи"].astype("str")+"</b>"
    folium.GeoJson(final_data[["district","geometry","Случаи","Прирост","Color"]].to_json(),style_function=lambda x: {'fillColor':x["properties"]["Color"],
                                                         'fillOpacity': 0.7, 'opacity': 0.7},
                           highlight_function=lambda x: {"fillOpacity": 0.3, "opacity": 0.3},zoom_on_click=False,
                           tooltip=folium.features.GeoJsonTooltip(fields=["district","Случаи","Прирост"],aliases=["","",""],style=("background-color:FFFFCC;color:black;font-family:Cambria; font-size:16px; padding: 10px;"))).add_to(m)

    a = """
        {% macro html(this, kwargs) %}

        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Карта</title>
          <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">

          <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
          <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>

          <script>
          $( function() {
            $( "#maplegend" ).draggable({
                            start: function (event, ui) {
                                $(this).css({
                                    right: "auto",
                                    top: "auto",
                                    bottom: "auto"
                                });
                            }
                        });
        });

          </script>
        </head>
        <body>


        <div id='maplegend' class='maplegend' 
            style='position:absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
             border-radius:6px; padding: 10px; font-size:16px; right: 20px; bottom: 20px;'>"""


    b = """<div class='legend-title'><b>Случаев</b></div>
        <div class='legend-scale'>
          <ul class='legend-labels'>
            <li><span style='background:#19ff19;opacity:0.7;'></span>не более {}</li>
            <li><span style='background:#faa307;opacity:0.7;'></span>от {} и не более {}</li>
            <li><span style='background:#e85d04;opacity:0.7;'></span>от {} и не более {}</li>
            <li><span style='background:#DC143C;opacity:0.7;'></span>от {} и не более {}</li>
            <li><span style='background:#ff0000;opacity:0.7;'></span>от {}</li>
          </ul>
        </div>
        </div>""".format(int(np.round(q[0])),int(np.round(q[0])),int(np.round(q[1])),int(np.round(q[1])),int(np.round(q[2])),int(np.round(q[2])),int(np.round(q[3])),int(np.round(q[3])))

    z = """</body>
        </html>

        <style type='text/css'>
          .maplegend .legend-title {
            text-align: left;
            margin-bottom: 5px;
            font-weight: bold;
            font-size: 90%;
            }
          .maplegend .legend-scale ul {
            margin: 0;
            margin-bottom: 5px;
            padding: 0;
            float: left;
            list-style: none;
            }
          .maplegend .legend-scale ul li {
            font-size: 80%;
            list-style: none;
            margin-left: 0;
            line-height: 18px;
            margin-bottom: 2px;
            }
          .maplegend ul.legend-labels li span {
            display: block;
            float: left;
            height: 16px;
            width: 30px;
            margin-right: 5px;
            margin-left: 0;
            border: 1px solid #999;
            }
          .maplegend .legend-source {
            font-size: 80%;
            color: #777;
            clear: both;
            }
          .maplegend a {
            color: #777;
            }
        </style>
        {% endmacro %}"""
    macro = MacroElement()
    macro._template = Template(a + b + z)
    m.add_child(macro)
    title_html = '''
             <h3 align="center" style="font-size:16px">
             <b>Карта распространения коронавируса в Республике Татарстан на {}</b> <br/>
             <a target="_blank" rel="noopener noreferrer" href="https://dashboardcovid19forsite.herokuapp.com/"> 
             Графики выявленных случаев </a>
             </h3>
             '''.format(dt.now().strftime("%d.%m.%Y"))
    m.get_root().html.add_child(folium.Element(title_html))
    m.save(MAP_PATH.format(dt.now().strftime("%d.%m.%Y")))
    m.save(MAP_GPATH.format(dt.now().strftime("%d.%m.%Y")))
    open(PHP_PATH,"w").close()
    with open(PHP_PATH,"w") as s:
        s.write('<?php include_once("Maps/index_{}.html"); ?>'.format(dt.now().strftime("%d.%m.%Y")))
    add_overhidden()


def update_tatinform(href):
    covid_prev_data=pd.read_excel(DATA_PATH.format((dt.now()-timedelta(days=1)).strftime("%d.%m.%Y")))
    covid_prev_data["Прирост"]=0
    raw_data=r.get(href).text.replace("<br/>"," ")
    soup=BeautifulSoup(raw_data,"lxml")
    stats=soup.find_all("div",{"class":"pi_text"})[0].text.split("География")[1]
    stats=re.findall(r"[А-Я]+[а-я]{2,}\s?–?\s?\d{1,}",stats)
    regs=[re.search(r"([А-Я]+[а-я]{2,})\s–?\s?\d{1,}",i).group(1) for i in stats]
    cases=[int(re.search(r"[А-Я]+[а-я]{2,}\s–?\s?(\d{1,})",i).group(1)) for i in stats]
    covid_prev_data.set_index("Район",inplace=True)
    for ind,val in enumerate(regs):
        if val=="Челны":
            val="Набережные Челны"
        elif val=="Устьинский":
            val="Камско-Устьинский"
        elif val=="Слободский":
            val="Рыбно-Слободский"
        covid_prev_data.loc[val,"Случаи"]+=cases[ind]
        covid_prev_data.loc[val,"Прирост"]+=cases[ind]
    covid_prev_data.reset_index(inplace=True)
    print(covid_prev_data["Прирост"].sum())
    covid_prev_data[["Район","Случаи"]].to_excel(
        DATA_PATH.format(dt.now().strftime("%d.%m.%Y")),index=False)
    covid_prev_data[["Район","Случаи"]].to_excel(
        DATA_GPATH.format(dt.now().strftime("%d.%m.%Y")),index=False)   
                           
    return covid_prev_data






#Для вестника камаза
def update_kamaz(href):
    covid_prev_data=pd.read_excel(DATA_PATH.format((dt.now()-timedelta(days=1)).strftime("%d.%m.%Y")))
    #print(covid_prev_data.values)
    covid_prev_data["Прирост"]=0
    raw_data=r.get(href).text
    soup=BeautifulSoup(raw_data,"lxml")
    stats=soup.find_all("p")[0].text.split(":")[1]
    stats=re.findall(r"[а-яА-Я]*\s?[-–]\s?\d{1,}",stats)
    regs=[re.search(r"([а-яА-Я]*)\s[-–]\s?\d{1,}",i).group(1) for i in stats]
    cases=[int(re.search(r"[а-яА-Я]*\s[-–]\s?(\d{1,})",i).group(1)) for i in stats]
    covid_prev_data.set_index("Район",inplace=True)
    for ind,val in enumerate(regs):
        if val=="Челны":
            val="Набережные Челны"
        elif val=="Устьинский":
            val="Камско-Устьинский"
        elif val=="Слободский":
            val="Рыбно-Слободский"
        covid_prev_data.loc[val,"Случаи"]+=cases[ind]
        covid_prev_data.loc[val,"Прирост"]+=cases[ind]
    covid_prev_data.reset_index(inplace=True)
    print(covid_prev_data["Прирост"].sum())
    covid_prev_data[["Район","Случаи"]].to_excel(
        DATA_GPATH.format(dt.now().strftime("%d.%m.%Y")),index=False)
    covid_prev_data[["Район","Случаи"]].to_excel(
        DATA_PATH.format(dt.now().strftime("%d.%m.%Y")),index=False)
    return covid_prev_data

def update_database():
    conn=sqlalchemy.create_engine('mysql://root:1806@localhost:3306/covid_tatarstan?charset=utf8mb4')
    metadata=sqlalchemy.MetaData()
    stats=sqlalchemy.Table("statistics",metadata,autoload=True,autoload_with=conn)
    vals=[]
    excel=pd.read_excel(DATA_PATH.format(dt.now().strftime("%d.%m.%Y")))
    i=(date(dt.now().year,dt.now().month,dt.now().day)-date(2020,12,17)).days*45
    for val in excel.itertuples():
        dic={}
        i=i+1
        if val[1] not in ["Казань","Набережные Челны"]:
            distr=val[1]+" район"
        else:
            distr="городской округ "+val[1]
        cases=val[2]
        dic["ID"]=i
        dic["District"]=distr
        dic["Cases"]=cases
        dic["Date"]=dt.now().strftime("%Y.%m.%d")
        vals.append(dic)
    ins=sqlalchemy.insert(stats)
    conn.execute(ins,vals)





