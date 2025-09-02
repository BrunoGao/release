import osmnx as ox
import networkx as nx
import shapely.geometry
import random
import folium
from folium import IFrame

# 设置要获取道路拓扑图的区域
polygon = shapely.geometry.Polygon([
    (114.049683, 22.547668),
    (114.050060, 22.529783),
    (114.071141, 22.529544),
    (114.072906, 22.531304),
    (114.072341, 22.547907)
])

# 获取道路拓扑图
graph = ox.graph_from_polygon(polygon, network_type='drive')

# 提取节点和边
nodes, edges = ox.graph_to_gdfs(graph)

# 随机选择一些节点作为人的位置
people_locations = random.sample(list(nodes.index), 10)  # 选择10个位置

# 健康信息
health_data = [
    {
        "name": "林欣稷",
        "job": "矿工",
        "id": "0115962",
        "group": "班组A",
        "phone": "13545678956",
        "status": "正常",
        "heart_rate": "76 bpm",
        "blood_pressure": "121/73 mmHg",
        "oxygen": "98 SaO2",
        "co": "60 ppm",
        "methane": "59 ppm",
        "oxygen_gas": "91 ppm"
    }
] * 10  # 为了简化示例，重复相同的数据

# 创建 folium 地图，没有地图背景层
m = folium.Map(location=[22.54, 114.06], zoom_start=14, tiles=None)

# 添加道路拓扑图，使用CSS3伪类模拟管状效果
for u, v, key, data in graph.edges(keys=True, data=True):
    x = [graph.nodes[u]['y'], graph.nodes[v]['y']]
    y = [graph.nodes[u]['x'], graph.nodes[v]['x']]
    folium.PolyLine(list(zip(x, y)), color="blue", weight=5, opacity=1).add_to(m)

# 读取自定义图标
icon_url = "static/images/blue-icon.png"

# 添加人的位置
for idx, node in enumerate(people_locations):
    x, y = nodes.loc[node, ['y', 'x']]
    data = health_data[idx]
    html = f"""
<!DOCTYPE html>
    <html>
      <head>
        <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css">
        <title>健康监测信息</title>
        <style>
          .body{{color: #6F8BA4;}}
          .section {{padding: 20px; position: relative;}}
          .gray-bg {{background-color: #f5f5f5;}}
          img {{max-width: 100%;}}
          img {{vertical-align: middle; border-style: none;}}
          .about-text h3 {{font-size: 20px; font-weight: 700; margin: 0 0 6px;}}
          .about-text h6 {{font-weight: 600; margin-bottom: 15px;}}
          .about-text p {{font-size: 18px; max-width: 450px;}}
          .about-text p mark {{font-weight: 600; color: #20247b;}}
          .about-list {{padding-top: 10px;}}
          .about-list .media {{padding: 5px 0;}}
          .about-list label {{color: #20247b; font-weight: 600; width: 88px; margin: 0; position: relative;}}
          .about-list label:after {{content: ""; position: absolute; top: 0; bottom: 0; right: 11px; width: 1px; height: 12px; background: #20247b; transform: rotate(15deg); margin: auto; opacity: 0.5;}}
          .about-list p {{margin: 0; font-size: 15px;}}
          .about-avatar img {{border-radius: 50%; width: 100px; height: 100px;}}
        </style>
      </head>
      <body>
        <section class="section about-section gray-bg" id="about">
          <div class="container">
              <div class="row align-items-center flex-row-reverse">
                  <div class="col-lg-6">
                      <div class="about-text go-to">
                          <h3 class="dark-color">{data['name']} {data['job']}</h3>
                          <h6 class="theme-color lead">健康监测信息</h6>
                          <div class="row about-list">
                           
                              <div class="col-md-6">
                                  <div class="media">
                                      <label>Heart Rate</label>
                                      <p>{data['heart_rate']}</p>
                                  </div>
                                  <div class="media">
                                      <label>Blood Pressure</label>
                                      <p>{data['blood_pressure']}</p>
                                  </div>
                                  <div class="media">
                                      <label>Oxygen</label>
                                      <p>{data['oxygen']}</p>
                                  </div>
                                  <div class="media">
                                      <label>CO</label>
                                      <p>{data['co']}</p>
                                  </div>
                                  <div class="media">
                                      <label>Methane</label>
                                      <p>{data['methane']}</p>
                                  </div>
                                  <div class="media">
                                      <label>Oxygen Gas</label>
                                      <p>{data['oxygen_gas']}</p>
                                  </div>
                              </div>
                          </div>
                      </div>
                  </div>
                  <div class="col-lg-6">
                      <div class="about-avatar">
                          <img src="{icon_url}" title="" alt="">
                      </div>
                  </div>
              </div>
               <div class="counter">
              <div class="row">
                  <div class="col-6 col-lg-3">
                      <div class="count-data text-center">
                          <h6 class="count h2" data-to="500" data-speed="500">500</h6>
                          <p class="m-0px font-w-600">{data['co']}</p>
                      </div>
                  </div>
                  <div class="col-6 col-lg-3">
                      <div class="count-data text-center">
                          <h6 class="count h2" data-to="150" data-speed="150">150</h6>
                          <p class="m-0px font-w-600">{data['oxygen_gas']}</p>
                      </div>
                  </div>
                  <div class="col-6 col-lg-3">
                      <div class="count-data text-center">
                          <h6 class="count h2" data-to="850" data-speed="850">850</h6>
                          <p class="m-0px font-w-600">{data['methane']}</p>
                      </div>
                  </div>
                  <div class="col-6 col-lg-3">
                      <div class="count-data text-center">
                          <h6 class="count h2" data-to="190" data-speed="190">190</h6>
                          <p class="m-0px font-w-600">Telephonic Talk</p>
                      </div>
                  </div>
              </div>
          </div>
          </div>
      </section>
      </body>
    </html>
    """
    iframe = IFrame(html, width=300, height=200)
    popup = folium.Popup(iframe, max_width=300)
    icon = folium.CustomIcon(icon_url, icon_size=(20, 20))
    folium.Marker([x, y], popup=popup, icon=icon).add_to(m)

# 保存地图
m.save("interactive_pipeline_map.html")

# 通过CSS添加管状效果
map_css = """
<style>
.leaflet-interactive {
    filter: drop-shadow(0 0 5px rgba(0, 0, 255, 0.5));
}
</style>
"""
with open("interactive_pipeline_map.html", "a") as file:
    file.write(map_css)