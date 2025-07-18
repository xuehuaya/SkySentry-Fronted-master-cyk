<template>
  <div class="project-layer-wrapper height-100">
    <div style="height: 50px; line-height: 50px; border-bottom: 1px solid #4f4f4f; font-weight: 450;">
      <a-row>
        <a-col :span="1"></a-col>
        <a-col :span="22">Annotations</a-col>
        <a-col :span="1"></a-col>
      </a-row>
    </div>
    <div class="scrollbar" :style="{ height: scorllHeight + 'px' }">
      <LayersTree
        :layer-data="mapLayers"
        class="project-layer-content"
        @check="checkLayer"
        @select="selectLayer"
        v-model:selectedKeys="selectedKeys"
        v-model:checkedKeys="checkedKeys"
      />
    </div>
    <a-drawer
      title="Map Element"
      placement="right"
      :closable="true"
      v-model:visible="visible"
      :mask="false"
      wrapClassName="drawer-element-wrapper"
      @close="closeDrawer"
      width="300"
    >
      <div class="drawer-element-content">
        <div class="name element-item">
          <span class="title">Name:</span>
          <a-input
            v-model:value="layerState.layerName"
            style="width:120px"
            placeholder="element name"
            @blur="changeLayer"
          />
        </div>
        <div
          class="longitude element-item"
          v-if="layerState.currentType === geoType.Point"
        >
          <span class="title">Longitude:</span>
          <a-input
            v-model:value="layerState.longitude"
            style="width:120px"
            placeholder="longitude"
            @blur="changeLayer"
          />
        </div>
        <div
          class="latitude element-item"
          v-if="layerState.currentType === geoType.Point"
        >
          <span class="title">Latitude:</span>
          <a-input
            v-model:value="layerState.latitude"
            style="width:120px"
            placeholder="latitude"
            @blur="changeLayer"
          />
        </div>
        <div class="color-content">
          <span class="mr30">Color: </span>
          <div
            v-for="item in colors"
            :key="item.id"
            class="color-item"
            :style="'background:' + item.color"
            @click="changeColor(item)"
            :class="{ selected: item.color === layerState.color }"
          >
            <svg-icon
              v-if="item.color === layerState.color"
              :size="18"
              name="check"
            ></svg-icon>
          </div>
        </div>
        <div class="mt20" style="text-align:center;">
          <a-button type="primary" @click="exportSelectedElementToKml">导出为 KMZ</a-button>
        </div>
      </div>
      <div class="flex-row flex-justify-around flex-align-center mt20">
        <a-popconfirm
          title="删除后不可恢复，确认删除吗？"
          ok-text="确定"
          cancel-text="取消"
          @confirm="deleteElement"
        >
          <a-button type="primary" danger>Delete</a-button>
        </a-popconfirm>
      </div>
    </a-drawer>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, reactive, ref, watch } from 'vue'
import JSZip from 'jszip'
import {
  deleteElementReq,
  getElementGroupsReq,
  updateElementsReq
} from '/@/api/layer'
import LayersTree from '/@/components/LayersTree.vue'
import { MapDoodleColor, MapElementEnum } from '/@/constants/map'
import { useGMapCover } from '/@/hooks/use-g-map-cover'
import { getRoot } from '/@/root'
import { useMyStore } from '/@/store'
import { GeojsonCoordinate, LayerResource } from '/@/types/map'
import { Color, GeoType } from '/@/types/mapLayer'
import { generatePoint } from '/@/utils/genjson'
import { gcj02towgs84, wgs84togcj02 } from '/@/vendors/coordtransform'
import { message } from 'ant-design-vue'

const root = getRoot()
const store = useMyStore()
let useGMapCoverHook = useGMapCover(store)
const mapLayers = ref(store.state.Layers)
const checkedKeys = ref<string[]>([])
const selectedKeys = ref<string[]>([])
const selectedKey = ref<string>('')
const selectedLayer = ref<LayerResource | null>(null)
const visible = ref<boolean>(false)
store.commit('SET_DRAW_VISIBLE_INFO', visible.value)
const geoType = GeoType
const layerState = reactive({
  layerName: '',
  layerId: '',
  longitude: 0,
  latitude: 0,
  currentType: '', // “LineString”,"Polygon","Point"
  color: '#212121'
})
const colors = ref<Color[]>([
  { id: 1, name: 'BLUE', color: '#2D8CF0', selected: true },
  { id: 2, name: 'GREEN', color: '#19BE6B', selected: false },
  { id: 3, name: 'YELLOW', color: '#FFBB00', selected: false },
  { id: 4, name: 'ORANGE', color: '#B620E0', selected: false },
  { id: 5, name: 'RED', color: '#E23C39', selected: false },
  { id: 6, name: 'NAME_DEFAULT', color: '#212121', selected: false }
])
const scorllHeight = ref<number>()

async function getAllElement () {
  getElementGroups('init')
  setTimeout(() => {
    useGMapCoverHook = useGMapCover()
    initMapCover()
  }, 1000)
}
function initMapCover () {
  mapLayers.value.forEach(item => {
    if (item.elements) {
      setMapCoverByElement(item.elements)
    }
  })
}
watch(
  () => store.state.Layers,
  (newData) => {
    mapLayers.value = newData
  },
  { deep: true }
)
function setMapCoverByElement (elements: LayerResource[]) {
  elements.forEach(element => {
    const name = element.name
    const color = element.resource?.content.properties.color
    updateMapElement(element, name, color)
  })
}
function updateMapElement (
  element: LayerResource,
  name: string,
  color: string | undefined
) {
  const geoTypeVal = element.resource?.content.geometry.type
  const id = element.id
  const type = element.resource?.type as number
  if (MapElementEnum.PIN === type) {
    const coordinates = element.resource?.content.geometry.coordinates as GeojsonCoordinate
    useGMapCoverHook.updatePinElement(id, name, coordinates, color)
  } else if (MapElementEnum.LINE === type && geoTypeVal === 'LineString') {
    const coordinates = element.resource?.content.geometry.coordinates as GeojsonCoordinate[]
    useGMapCoverHook.updatePolylineElement(id, name, coordinates, color)
  } else if (MapElementEnum.POLY === type && geoTypeVal === 'Polygon') {
    const coordinates = element.resource?.content.geometry.coordinates as GeojsonCoordinate[][]
    useGMapCoverHook.updatePolygonElement(id, name, coordinates, color)
  }
}
function checkLayer (keys: string[]) {
  console.log('checkLayer', keys, selectedKeys.value, checkedKeys.value)
}
function selectLayer (keys: string[], e) {
  if (e.selected) {
    selectedKey.value = e.node.eventKey
    selectedLayer.value = getCurrentLayer(selectedKey.value)
    setBaseInfo()
  }
  visible.value = e.selected
  store.commit('SET_DRAW_VISIBLE_INFO', visible.value)
}
function getCurrentLayer (id: string) {
  const Layers = store.state.Layers
  const key = id.replaceAll('resource__', '')
  let layer: LayerResource | null = null
  const findCan = function (V: LayerResource[]) {
    V.forEach(item => {
      if (item.id === key) {
        layer = item
      }
      if (item.elements) {
        findCan(item.elements)
      }
    })
  }
  findCan(Layers)
  return layer
}
function setBaseInfo () {
  const layer = selectedLayer.value
  if (layer) {
    const geoTypeVal = layer.resource?.content.geometry.type
    layerState.currentType = geoTypeVal
    layerState.layerName = layer.name
    layerState.layerId = layer.id
    layerState.color = layer.resource?.content.properties.color
    if (geoTypeVal === GeoType.Point) {
      const coordinate = gcj02towgs84(
        layer.resource?.content.geometry.coordinates[0],
        layer.resource?.content.geometry.coordinates[1]
      ) as GeojsonCoordinate
      layerState.longitude = coordinate[0]
      layerState.latitude = coordinate[1]
    }
  }
}
onMounted(() => {
  const element = document.getElementsByClassName('scrollbar').item(0) as HTMLDivElement
  const parent = element?.parentNode as HTMLDivElement
  scorllHeight.value = parent?.clientHeight - parent.firstElementChild!.clientHeight
  getAllElement()
})
function closeDrawer () {
  store.commit('SET_DRAW_VISIBLE_INFO', false)
  selectedKeys.value = []
}
function changeColor (color: Color) {
  layerState.color = color.color
  updateElements()
}
function validateCoordinates () {
  if (layerState.currentType !== geoType.Point) return true
  if (
    isNaN(Number(layerState.longitude)) ||
    Number(layerState.longitude) < -180 ||
    Number(layerState.longitude) > 180
  ) {
    message.error('经度必须在 -180 到 180 之间')
    return false
  }
  if (
    isNaN(Number(layerState.latitude)) ||
    Number(layerState.latitude) < -90 ||
    Number(layerState.latitude) > 90
  ) {
    message.error('纬度必须在 -90 到 90 之间')
    return false
  }
  return true
}
async function changeLayer () {
  if (!validateCoordinates()) return
  await updateElements()
}
async function deleteElement () {
  if (!selectedLayer.value) return
  const elementid = selectedLayer.value.id
  await deleteElementReq(elementid, {}).then(async (res: any) => {
    if (res.code !== 0) {
      console.warn(res)
      return
    }
    visible.value = false
    store.commit('SET_DRAW_VISIBLE_INFO', visible.value)
    useGMapCoverHook.removeCoverFromMap(elementid)
    getAllElement()
  })
}
async function getElementGroups (type?: string) {
  const result = await getElementGroupsReq({
    groupId: '',
    isDistributed: true
  })
  mapLayers.value = result.data
  mapLayers.value = updateWgs84togcj02()
  if (type && type === 'init') {
    store.dispatch('setLayerInfo', mapLayers.value)
  }
  store.commit('SET_LAYER_INFO', mapLayers.value)
}
async function updateElements () {
  if (!selectedLayer.value) return
  let content = null
  if (layerState.currentType === GeoType.Point) {
    const position = {
      height: 0,
      latitude: Number(layerState.latitude || 0),
      longitude: Number(layerState.longitude || 0)
    }
    const cxt = generatePoint(position, {
      color: layerState.color || MapDoodleColor.PinColor,
      clampToGround: true
    })
    content = {
      type: MapElementEnum.PIN,
      geometry: cxt.geometry,
      properties: cxt.properties
    }
    const currentLayer = selectedLayer.value
    currentLayer.resource.content = content
    selectedLayer.value = currentLayer
  } else {
    const currentLayer = selectedLayer.value
    content = currentLayer.resource.content
    content.properties.color = layerState.color
  }
  updateMapElement(selectedLayer.value, layerState.layerName, layerState.color)
  await updateElementsReq(layerState.layerId, {
    name: layerState.layerName,
    content: content
  })
  getAllElement()
}
function updateWgs84togcj02 () {
  const layers = mapLayers.value
  layers.forEach(item => {
    if (item.elements) {
      item.elements.forEach(ele => {
        updateCoordinates('wgs84-gcj02', ele)
      })
    }
  })
  return layers
}
function updateCoordinates (transformType: string, element: LayerResource) {
  const geoTypeVal = element.resource?.content.geometry.type
  const type = element.resource?.type as number
  if (element.resource) {
    if (MapElementEnum.PIN === type) {
      const coordinates = element.resource?.content.geometry.coordinates as GeojsonCoordinate
      if (transformType === 'wgs84-gcj02') {
        const transResult = wgs84togcj02(coordinates[0], coordinates[1]) as GeojsonCoordinate
        element.resource.content.geometry.coordinates = transResult
      } else if (transformType === 'gcj02-wgs84') {
        const transResult = gcj02towgs84(coordinates[0], coordinates[1]) as GeojsonCoordinate
        element.resource.content.geometry.coordinates = transResult
      }
    } else if (MapElementEnum.LINE === type) {
      const coordinates = element.resource?.content.geometry.coordinates as GeojsonCoordinate[]
      if (transformType === 'wgs84-gcj02') {
        coordinates.forEach((coordinate, i, arr) => {
          arr[i] = wgs84togcj02(coordinate[0], coordinate[1]) as GeojsonCoordinate
        })
      } else if (transformType === 'gcj02-wgs84') {
        coordinates.forEach((coordinate, i, arr) => {
          arr[i] = gcj02towgs84(coordinate[0], coordinate[1]) as GeojsonCoordinate
        })
      }
      element.resource.content.geometry.coordinates = coordinates
    } else if (MapElementEnum.POLY === type) {
      const coordinates = element.resource?.content.geometry.coordinates[0] as GeojsonCoordinate[]
      if (transformType === 'wgs84-gcj02') {
        coordinates.forEach((coordinate, i, arr) => {
          arr[i] = wgs84togcj02(coordinate[0], coordinate[1]) as GeojsonCoordinate
        })
      } else if (transformType === 'gcj02-wgs84') {
        coordinates.forEach((coordinate, i, arr) => {
          arr[i] = gcj02towgs84(coordinate[0], coordinate[1]) as GeojsonCoordinate
        })
      }
      element.resource.content.geometry.coordinates = [coordinates]
    }
  }
}

// ====== 修改后的导出 KMZ (WPML格式)功能 ======

// 将几何信息转换为航点列表
function convertGeometryToWaypoints (geometry: any): Array<{lon: number, lat: number}> {
  const waypoints: Array<{lon: number, lat: number}> = []

  if (!geometry || !geometry.coordinates) {
    return waypoints
  }

  const type = geometry.type

  if (type === 'Point') {
    // 单点
    const [lon, lat] = geometry.coordinates
    waypoints.push({ lon, lat })
  } else if (type === 'LineString') {
    // 线路 - 将线上的点作为航点
    geometry.coordinates.forEach((coord: number[]) => {
      const [lon, lat] = coord
      waypoints.push({ lon, lat })
    })
  } else if (type === 'Polygon') {
    // 多边形 - 将外环的点作为航点
    const ring = geometry.coordinates[0] // 取外环
    ring.forEach((coord: number[], index: number) => {
      // 跳过最后一个点（与第一个点重复）
      if (index < ring.length - 1) {
        const [lon, lat] = coord
        waypoints.push({ lon, lat })
      }
    })
  }

  return waypoints
}

// 生成单个航点的WPML格式
function generateWaypointPlacemark (waypoint: {lon: number, lat: number}, index: number): string {
  const executeHeight = 100 // 默认飞行高度100米，可以根据需要调整
  const waypointSpeed = index === 0 ? 10 : 7 // 第一个点速度10m/s，其他点7m/s

  return `
      <Placemark>
        <Point>
          <coordinates>${waypoint.lon},${waypoint.lat}</coordinates>
        </Point>
        <wpml:index>${index}</wpml:index>
        <wpml:executeHeight>${executeHeight}</wpml:executeHeight>
        <wpml:waypointSpeed>${waypointSpeed}</wpml:waypointSpeed>
        <wpml:waypointHeadingParam>
          <wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode>
        </wpml:waypointHeadingParam>
        <wpml:waypointTurnParam>
          <wpml:waypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:waypointTurnMode>
          <wpml:waypointTurnDampingDist>0</wpml:waypointTurnDampingDist>
        </wpml:waypointTurnParam>
        ${index === 1 ? generateActionGroup() : ''}
      </Placemark>`
}

// 生成动作组（在第二个航点添加拍照动作）
function generateActionGroup (): string {
  return `
        <wpml:actionGroup>
          <wpml:actionGroupId>0</wpml:actionGroupId>
          <wpml:actionGroupStartIndex>1</wpml:actionGroupStartIndex>
          <wpml:actionGroupEndIndex>1</wpml:actionGroupEndIndex>
          <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
          <wpml:actionTrigger>
            <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
          </wpml:actionTrigger>
          <wpml:action>
            <wpml:actionId>0</wpml:actionId>
            <wpml:actionActuatorFunc>gimbalRotate</wpml:actionActuatorFunc>
            <wpml:actionActuatorFuncParam>
              <wpml:gimbalRotateMode>absoluteAngle</wpml:gimbalRotateMode>
              <wpml:gimbalPitchRotateEnable>0</wpml:gimbalPitchRotateEnable>
              <wpml:gimbalPitchRotateAngle>0</wpml:gimbalPitchRotateAngle>
              <wpml:gimbalRollRotateEnable>0</wpml:gimbalRollRotateEnable>
              <wpml:gimbalRollRotateAngle>0</wpml:gimbalRollRotateAngle>
              <wpml:gimbalYawRotateEnable>1</wpml:gimbalYawRotateEnable>
              <wpml:gimbalYawRotateAngle>30</wpml:gimbalYawRotateAngle>
              <wpml:gimbalRotateTimeEnable>0</wpml:gimbalRotateTimeEnable>
              <wpml:gimbalRotateTime>0</wpml:gimbalRotateTime>
              <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>
            </wpml:actionActuatorFuncParam>
          </wpml:action>
          <wpml:action>
            <wpml:actionId>1</wpml:actionId>
            <wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc>
            <wpml:actionActuatorFuncParam>
              <wpml:fileSuffix>point${1}</wpml:fileSuffix>
              <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>
            </wpml:actionActuatorFuncParam>
          </wpml:action>
        </wpml:actionGroup>`
}
// ====== 新增导出 KMZ (WPML格式)功能 ======

async function exportSelectedElementToKml () {
  if (!selectedLayer.value) {
    message.warning('请先选中一个地图元素')
    return
  }

  const name = layerState.layerName || 'Element'
  const color = layerState.color || '#212121'
  const geometry = selectedLayer.value.resource?.content.geometry

  if (!geometry) {
    message.warning('该元素没有有效几何信息')
    return
  }

  const nowStr = new Date().toISOString()
  const timestamp = Date.now() // 当前时间戳，用于创建时间

  // 颜色转换为KML颜色格式 AABBGGRR
  const hexColor = color.replace('#', '')
  const r = hexColor.substr(0, 2)
  const g = hexColor.substr(2, 2)
  const b = hexColor.substr(4, 2)
  const kmlColor = `ff${b}${g}${r}` // KML颜色格式为AABBGGRR

  // 生成KML几何元素的函数（用于template.kml）
  function generateKmlGeometry (geometry: any): string {
    const type = geometry.type
    if (type === 'Point') {
      const coords = geometry.coordinates.join(',') + ',0'
      return `<Point><coordinates>${coords}</coordinates></Point>`
    }
    if (type === 'LineString') {
      const coords = geometry.coordinates.map((c: number[]) => c.join(',') + ',0').join(' ')
      return `<LineString><coordinates>${coords}</coordinates></LineString>`
    }
    if (type === 'Polygon') {
      const ring = geometry.coordinates[0]
      const coords = ring.map((c: number[]) => c.join(',') + ',0').join(' ')
      return `<Polygon><outerBoundaryIs><LinearRing><coordinates>${coords}</coordinates></LinearRing></outerBoundaryIs></Polygon>`
    }
    return ''
  }

  // template.kml（模板文件）- 保持原有格式
  const templateKmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.2">
  <Document>
    <wpml:author>DJI</wpml:author>
    <wpml:createTime>${timestamp}</wpml:createTime>
    <wpml:updateTime>${timestamp}</wpml:updateTime>

    <!-- Step 2: Setup Mission Configuration -->
    <wpml:missionConfig>
      <wpml:flyToWaylineMode>safely</wpml:flyToWaylineMode>
      <wpml:finishAction>goHome</wpml:finishAction>
      <wpml:exitOnRCLost>goContinue</wpml:exitOnRCLost>
      <wpml:executeRCLostAction>hover</wpml:executeRCLostAction>
      <wpml:takeOffSecurityHeight>20</wpml:takeOffSecurityHeight>
      <wpml:takeOffRefPoint>23.98057,115.987663,100</wpml:takeOffRefPoint>
      <wpml:takeOffRefPointAGLHeight>35</wpml:takeOffRefPointAGLHeight>
      <wpml:globalTransitionalSpeed>8</wpml:globalTransitionalSpeed>
      <wpml:droneInfo>
        <wpml:droneEnumValue>67</wpml:droneEnumValue>
        <wpml:droneSubEnumValue>0</wpml:droneSubEnumValue>
      </wpml:droneInfo>
      <wpml:payloadInfo>
        <wpml:payloadEnumValue>52</wpml:payloadEnumValue>
        <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>
      </wpml:payloadInfo>
    </wpml:missionConfig>

    <!-- Step 3: Setup A Folder for Waypoint Template -->
    <Folder>
      <wpml:templateType>waypoint</wpml:templateType>
      <wpml:templateId>0</wpml:templateId>
      <wpml:waylineCoordinateSysParam>
        <wpml:coordinateMode>WGS84</wpml:coordinateMode>
        <wpml:heightMode>EGM96</wpml:heightMode>
        <wpml:globalShootHeight>50</wpml:globalShootHeight>
        <wpml:positioningType>GPS</wpml:positioningType>
        <wpml:surfaceFollowModeEnable>1</wpml:surfaceFollowModeEnable>
        <wpml:surfaceRelativeHeight>100</wpml:surfaceRelativeHeight>
      </wpml:waylineCoordinateSysParam>
      <wpml:autoFlightSpeed>7</wpml:autoFlightSpeed>
      <wpml:gimbalPitchMode>usePointSetting</wpml:gimbalPitchMode>
      <wpml:globalWaypointHeadingParam>
        <wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode>
        <wpml:waypointHeadingAngle>45</wpml:waypointHeadingAngle>
        <wpml:waypointPoiPoint>24.323345,116.324532,31.000000</wpml:waypointPoiPoint>
        <wpml:waypointHeadingPathMode>clockwise</wpml:waypointHeadingPathMode>
      </wpml:globalWaypointHeadingParam>
      <wpml:globalWaypointTurnMode>toPointAndStopWithDiscontinuityCurvature</wpml:globalWaypointTurnMode>
      <wpml:globalUseStraightLine>0</wpml:globalUseStraightLine>

      <!-- First Waypoint -->
      <Placemark>
        <Point>
          <coordinates>${layerState.longitude},${layerState.latitude},0</coordinates>
        </Point>
        <wpml:index>0</wpml:index>
        <wpml:executeHeight>100</wpml:executeHeight>
        <wpml:ellipsoidHeight>90.2</wpml:ellipsoidHeight>
        <wpml:height>100</wpml:height>
        <wpml:useGlobalHeight>1</wpml:useGlobalHeight>
        <wpml:useGlobalSpeed>1</wpml:useGlobalSpeed>
        <wpml:useGlobalHeadingParam>1</wpml:useGlobalHeadingParam>
        <wpml:useGlobalTurnParam>1</wpml:useGlobalTurnParam>
        <wpml:gimbalPitchAngle>0</wpml:gimbalPitchAngle>
      </Placemark>

      <!-- Second Waypoint -->
      <Placemark>
        <Point>
          <coordinates>${layerState.longitude},${layerState.latitude},0</coordinates>
        </Point>
        <wpml:index>1</wpml:index>
        <wpml:executeHeight>100</wpml:executeHeight>
        <wpml:ellipsoidHeight>90.2</wpml:ellipsoidHeight>
        <wpml:height>100</wpml:height>
        <wpml:useGlobalHeight>1</wpml:useGlobalHeight>
        <wpml:useGlobalSpeed>1</wpml:useGlobalSpeed>
        <wpml:useGlobalHeadingParam>1</wpml:useGlobalHeadingParam>
        <wpml:useGlobalTurnParam>1</wpml:useGlobalTurnParam>
        <wpml:gimbalPitchAngle>0</wpml:gimbalPitchAngle>

        <!-- Action group for waypoint -->
        <wpml:actionGroup>
          <wpml:actionGroupId>0</wpml:actionGroupId>
          <wpml:actionGroupStartIndex>1</wpml:actionGroupStartIndex>
          <wpml:actionGroupEndIndex>1</wpml:actionGroupEndIndex>
          <wpml:actionGroupMode>sequence</wpml:actionGroupMode>
          <wpml:actionTrigger>
            <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>
          </wpml:actionTrigger>
          <wpml:action>
            <wpml:actionId>0</wpml:actionId>
            <wpml:actionActuatorFunc>gimbalRotate</wpml:actionActuatorFunc>
            <wpml:actionActuatorFuncParam>
              <wpml:gimbalYawRotateAngle>30</wpml:gimbalYawRotateAngle>
            </wpml:actionActuatorFuncParam>
          </wpml:action>
          <wpml:action>
            <wpml:actionId>1</wpml:actionId>
            <wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc>
            <wpml:actionActuatorFuncParam>
              <wpml:fileSuffix>point1</wpml:fileSuffix>
            </wpml:actionActuatorFuncParam>
          </wpml:action>
        </wpml:actionGroup>
      </Placemark>
    </Folder>
  </Document>
</kml>`

  // 将几何信息转换为航点
  const waypoints = convertGeometryToWaypoints(geometry)

  if (waypoints.length === 0) {
    message.warning('无法从该元素提取有效航点')
    return
  }

  // 生成航点列表
  const waypointPlacemarks = waypoints.map((waypoint, index) =>
    generateWaypointPlacemark(waypoint, index)
  ).join('')

  // waylines.wpml（执行文件）- 按照DJI标准格式
  const waylinesWpmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.2">
  <Document>
    <!-- Step 1: Setup Mission Configuration -->
    <wpml:missionConfig>
      <wpml:flyToWaylineMode>safely</wpml:flyToWaylineMode>
      <wpml:finishAction>goHome</wpml:finishAction>
      <wpml:exitOnRCLost>goContinue</wpml:exitOnRCLost>
      <wpml:executeRCLostAction>hover</wpml:executeRCLostAction>
      <wpml:takeOffSecurityHeight>20</wpml:takeOffSecurityHeight>
      <wpml:globalTransitionalSpeed>10</wpml:globalTransitionalSpeed>
      <!-- Declare drone model with M30 -->
      <wpml:droneInfo>
        <wpml:droneEnumValue>67</wpml:droneEnumValue>
        <wpml:droneSubEnumValue>0</wpml:droneSubEnumValue>
      </wpml:droneInfo>
      <!-- Declare payload model with M30 -->
      <wpml:payloadInfo>
        <wpml:payloadEnumValue>52</wpml:payloadEnumValue>
        <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>
      </wpml:payloadInfo>
    </wpml:missionConfig>

    <!-- Step 2: Setup A Folder for Waypoint Template -->
    <Folder>
      <wpml:templateId>0</wpml:templateId>
      <wpml:executeHeightMode>WGS84</wpml:executeHeightMode>
      <wpml:waylineId>0</wpml:waylineId>
      <wpml:autoFlightSpeed>10</wpml:autoFlightSpeed>${waypointPlacemarks}
    </Folder>

  </Document>
</kml>`

  const zip = new JSZip()
  zip.file('template.kml', templateKmlContent)
  zip.file('waylines.wpml', waylinesWpmlContent)
  zip.folder('res') // 空资源文件夹，符合DJI标准

  const content = await zip.generateAsync({ type: 'blob' })

  const url = URL.createObjectURL(content)
  const a = document.createElement('a')
  a.href = url
  a.download = `${name}.kmz`
  a.click()
  URL.revokeObjectURL(url)

  message.success(`成功导出 ${name}.kmz 文件（包含 ${waypoints.length} 个航点）`)
}
</script>

<style lang="scss" scoped>
@import '/@/styles/index.scss';
</style>
<style lang="scss">
.drawer-element-wrapper {
  .ant-drawer-content {
    background-color: $dark-highlight;
    color: $text-white-basic;
    .ant-drawer-header {
      background-color: $dark-highlight;
      .ant-drawer-title {
        color: $text-white-basic;
      }
      .ant-drawer-close {
        color: $text-white-basic;
      }
    }
    .ant-input {
      background-color: #101010;
      border-color: $dark-border;
      color: $text-white-basic;
    }
  }
  .color-content {
    display: flex;
    align-items: center;
    margin-top: 8px;
    .color-item {
      cursor: pointer;
      width: 18px;
      height: 18px;
      line-height: 18px;
      display: flex;
      align-items: center;
      margin-left: 5px;
      border-radius: 2px;
      transition: border-color 0.3s ease;
    }
    .color-item.selected,
    .color-item:hover {
      border: 2px solid #fff;
    }
  }
  .title {
    display: inline-flex;
    width: 80px;
  }
  .element-item {
    margin-bottom: 10px;
  }
}
.scrollbar {
  overflow: auto;
}
.mt20 {
  margin-top: 20px;
}
</style>
