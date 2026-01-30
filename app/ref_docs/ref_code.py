try:
    #step 2. 한전 KDN 운영 서버 데이터 WFS 호출_전주정보
    node_layerName = "AI_FAC_001.GIS_LOC"; # 전주 레이어명
    meter = "430"; # 거리
    meter_line = "530";
    #node_url = 'http://192.168.0.71:8180/orange/wfs?GDX=SWEG_DC_GIS.xml' 
    node_url = gis
    headers = {"Content-Type": "text/xml", "Accept": "application/json"}
    node_propertyName = node_layerName.split('.')[1] #GIS_LOC

    #고압전선 호출
    power_high_layername = "AI_FAC_002.GIS_PTH"
    power_high_propertyName = power_high_layername.split('.')[1]

    #저압전선 호출
    power_low_layername = "AI_FAC_003.GIS_PTH"
    power_low_propertyName = power_low_layername.split('.')[1]
    
    #변압기(가공뱅크)호출
    power_bank_layername = "AI_FAC_004.GIS_LOC"
    power_bank_propertyName = power_bank_layername.split('.')[1]
    
    #도로중심선 호출 
    link_layerName = "AI_BASE_002.GIS_PTH_VAL"; 
    #main_url = 'http://192.168.0.71:8180/orange/wfs?GDX=SWEG_DC_BASE.xml'
    main_url = base
    link_propertyName = link_layerName.split('.')[1]
    
    #건물 db 호출
    build_layerName = "AI_BASE_004.GIS_AREA_VAL"; 
    build_propertyName = build_layerName.split('.')[1]
    
    #하천 db 호출
    river_layerName = "AI_BASE_005.GIS_AREA_VAL"; 
    river_propertyName = river_layerName.split('.')[1]
    
    #철도 db 호출
    train_layerName = "AI_BASE_003.GIS_AREA_VAL";
    train_propertyName = train_layerName.split('.')[1]

    #수부경계 db
    lake_layerName = "AI_BASE_006.GIS_AREA_VAL";
    lake_propertyName = lake_layerName.split('.')[1]

    view_high_layerName = "AI_VIEW_001"
    
    view_low_layerName = "AI_VIEW_002"

except Exception as e:
    def_list.handle_error('Unknown Error - not match db name')